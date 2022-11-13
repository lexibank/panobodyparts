from collections import defaultdict

from pathlib import Path
from pylexibank.dataset import Dataset as BaseDataset 
from pylexibank import Language, FormSpec, Concept
from pylexibank import progressbar

from clldutils.misc import slug
import attr
from pyedictor import fetch
from pylexibank import Lexeme
import lingpy

LANGUAGES = "Arara|Matses|Matis|Marubo|Shipibo_Konibo|Kapanawa|Shanenawa|Yawanawa|Nukini|Poyanawa|Iskonawa|Chakobo|Kakataibo|Kaxarari|Mastanawa|Chaninawa|Sharanawa|Amawaka|Nawa|Marinawa|Yaminawa|Kashinawa_P|Kashinawa_B|Araona|Katukina|Pakawara|Kanamari".split("|")
CONCEPTS = [
    'back [of body]', # 
    'belly', #
    'blood', #
    'bone', #
    'ear', #
    'eye', #
    'fat (grease)', #
    'feather [large]', #
    'foot', #
    'guts', #
    'hair',# 
    'hand', #
    'head', #
    'heart', #
    'leg', #
    'liver', #
    'meat (flesh)', #
    'mouth', #
    'neck', #
    'nose', #
    'skin [of person]', #
    'tail', #
    'tongue', #
    'tooth [front]', #
    'wing', #
]



@attr.s
class CustomLanguage(Language):
    SubGroup = attr.ib(default=None)
    Family = attr.ib(default='Pano')
    Note = attr.ib(default=None)
    SourceDate = attr.ib(default=None)
    Source = attr.ib(default=None)


@attr.s
class CustomConcept(Concept):
    Spanish_Gloss = attr.ib(default=None)


@attr.s
class CustomLexeme(Lexeme):
    Partial_Cognacy = attr.ib(default=None)
    Motivation_Structure = attr.ib(default=None)
    RootCognacy = attr.ib(default=None, metadata={
        "dc:description": "cognacy judged by the root",
        "format": "integer"})
    FormativeCognacy = attr.ib(default=None, metadata={
        "dc:description": "cognacy judged by the formative",
        "format": "integer"})


def desegment(tokens):
    out = []
    for t in tokens:
        if '.' in t:
            out += t.split('.')
        else:
            out += [t]
    return out


class Dataset(BaseDataset):
    dir = Path(__file__).parent
    id = "panobodyparts"
    language_class = CustomLanguage
    lexeme_class = CustomLexeme
    concept_class = CustomConcept
    form_spec = FormSpec(
            missing_data=("–", "-")
            )
    def cmd_download(self, args):
        args.log.info('updating ...')
        with open(self.raw_dir.joinpath("pano.tsv"), "w",
                encoding="utf-8") as f:
            f.write(fetch("pano", base_url="https://digling.org/edictor",
                languages=LANGUAGES, concepts=CONCEPTS))

        self.raw_dir.xlsx2csv("body-parts en pano.xlsx")

    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.
        """
        wl = lingpy.Wordlist(str(self.raw_dir / "pano.tsv"))
        concepts = {}
        for concept in self.concepts:
            if concept["ENGLISH"] in CONCEPTS:
                idx = concept["NUMBER"] + "_" + slug(concept["ENGLISH"])
                args.writer.add_concept(
                        ID=idx,
                        Name=concept["ENGLISH"],
                        Spanish_Gloss=concept["SPANISH"],
                        Concepticon_ID=concept["CONCEPTICON_ID"],
                        Concepticon_Gloss=concept["CONCEPTICON_GLOSS"]
                        )
                concepts[concept["ENGLISH"]] = idx
        for a, b in [
                ("corazon", "heart"),
                ("bellly", "belly"),
                ("grasa", "fat (grease)"),
                ("boca", "mouth"),
                ("carne", "meat (flesh)"),
                ]:
            concepts[a] = concepts[b]

        
        languages = {}
        for language in self.languages:
            if language["ID"] in LANGUAGES or language["Name"] in LANGUAGES:
                args.writer.add_language(**language)
                languages[language["ID"]] = language["ID"]
                languages[language["Name"]] = language["ID"]
                
        sources = {}
        for language in self.languages:
            sources[language["ID"]] = language["Source"]
            sources[language["Name"]] = language["Source"]
        args.writer.add_sources()

        # create secondary wordlist from other data
        data = {0: [
            "doculect", "concept", "value", "form", "tokens", "cogids",
            "cogid", "formid", "morphemes"]}
        
        corrected_paths = {
                "heart": "corazon",
                "mouth": "boca",
                "fat (grease)": "grasa",
                "meat (flesh)": "carne",
                "belly": "bellly",
                "tooth [front]": "tooth",
                "skin [of person]": "skin",
                "back [of body]": "back",
                "feather [large]": "feather",
                }
        for concept in CONCEPTS:
            pth = "body-parts en pano.{0}.csv".format(
                    corrected_paths.get(concept, concept))
            if not self.raw_dir.joinpath(pth).exists():
                args.log.info("missing concept «{0}»".format(concept))
                continue
            table = self.raw_dir.read_csv(pth)
            header = table[1]
            roots, formatives = {}, {}
            for i in range(len(table[0])):
                if table[0][i].strip() == "ROOT":
                    roots[i] = header[i]
                elif table[0][i].strip() == "FORMATIVE":
                    formatives[i] = header[i]
            # iterate over rows
            args.log.info("adding concept {0}".format(concept))
            for row_ in table[2:]:
                row = dict(zip(header, row_))
                if row["ID"]:
                    cogid, formative_id = 0, 0
                    for rootid, headid in roots.items():
                        if row[headid].strip() == "1":
                            cogid = int(headid)
                    for formid, headid in formatives.items():
                        if row[headid].strip() == "1":
                            formative_id = int(headid)

                    data[int(row["ID"])] = [
                            languages[row["DOCULECT"]],
                            row["CONCEPT"],
                            row["VALUE"],
                            row["FORM"],
                            row["TOKENS"],
                            row["COGIDS"],
                            cogid,
                            formative_id,
                            row["MORPHEMES"]]

        # look at differences
        wl2 = lingpy.Wordlist(data)
        for idx in wl2:
            args.writer.add_form_with_segments(
                    Parameter_ID=concepts[wl2[idx, "concept"]],
                    Language_ID=wl2[idx, "doculect"],
                    Value=wl2[idx, "value"],
                    Form=wl2[idx, "form"],
                    Segments=wl2[idx, "tokens"].split(),
                    RootCognacy=wl2[idx, 'cogid'],
                    FormativeCognacy=wl2[idx, "formid"],
                    Partial_Cognacy=str(lingpy.basictypes.ints(wl2[idx, "cogids"])) or 0,
                    Motivation_Structure=str(lingpy.basictypes.strings(wl2[idx, "morphemes"])) or "?",
                    Source=sources[wl2[idx, "doculect"]]
                    )


        #for idx in wl:
        #    args.writer.add_form_with_segments(
        #            Parameter_ID=concepts[wl[idx, "concept"]],
        #            Language_ID=wl[idx, "doculect"],
        #            Value=wl[idx, "value"],
        #            Form=wl[idx, "form"],
        #            Segments=desegment(wl[idx, "tokens"]),
        #            Cognacy=wl[idx, 'cogid'],
        #            Partial_Cognacy=str(lingpy.basictypes.ints(wl[idx, "cogids"])) or 0,
        #            Motivation_Structure=str(lingpy.basictypes.strings(wl[idx, "morphemes"])) or "?",
        #            Source=sources[wl[idx, "doculect"]]
        #            )

