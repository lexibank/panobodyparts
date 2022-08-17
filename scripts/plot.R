library(ape)
library(ggplot2)
library(dplyr)
library(ggrepel)
theme_set(theme_bw(base_size=14))

read <- function(filename) {
    if (length(grep("\\.delta\\.", filename)) == 1) {
        metric <- "Delta"
    } else if (length(grep("\\.qresidual\\.", filename)) == 1) {
        metric <- 'QResidual'
    }

    df <- read.delim(filename, header=FALSE, col.names=c("Language", "Score"))
    df$Metric <- metric
    df
}

data.f <- rbind(read('formativa.delta.dat'), read('formativa.qresidual.dat'))
data.r <- rbind(read('root.delta.dat'), read('root.qresidual.dat'))

data.f$Subset <- 'Formatives'
data.r$Subset <- 'Roots'


# 1. overall
data <- rbind(data.f, data.r)
ggplot(data[data$Metric == 'Delta',], aes(x=Score)) + geom_histogram() + facet_grid(Subset~.)
ggsave('histogram.pdf')

# 2. language?
dd <- left_join(
    data %>% filter(Metric == 'Delta' & Subset == 'Roots') %>% select(Language, Score) %>% rename(Roots=Score),
    data %>% filter(Metric == 'Delta' & Subset == 'Formatives') %>% select(Language, Score) %>% rename(Formatives=Score),
    by = "Language"
)

ggplot(dd, aes(x=Roots, y=Formatives, label=Language)) +
    geom_abline(slope=1, color="lightgray") +
    geom_point() +
    geom_text_repel() +
    xlim(0.35, 0.47) + ylim(0.35, 0.47)
ggsave('scatter.pdf')



cognatesizes <- function(nex) {
    df <- as.data.frame(nex)

    count <- function(arow) {
        length(arow[arow == '1'])
    }
    out <- data.frame(
        Site=row.names(df), Size=apply(df, 1, count)
    )
    out
}


nex.f <- read.nexus.data('formative.nex')
nex.r <- read.nexus.data('root.nex')

sizes.f <- cognatesizes(nex.f)
sizes.r <- cognatesizes(nex.r)

sizes.f$Subset <- 'Formatives'
sizes.r$Subset <- 'Roots'

sizes <- rbind(sizes.f, sizes.r)

ggplot(sizes, aes(Size, fill=Subset)) + geom_histogram() + facet_grid(Subset~.) + guides(fill="none")
ggsave("cognatesizes.pdf")
