library(ape)
library(treeio)
library(ggplot2)
library(ggtree)
library(ggnewscale)

tree <- treeio::read.newick('languages.nwk')

tree <- drop.tip(tree, c('Korubo', 'Kulina'))


roots <- c('ma', 'ßu', 'wi')
formatives <- c('pi', 'pu', 'ʂo', 'ʂka')

data <- read.csv('data.txt', header=TRUE, strip.white=TRUE, row.names=1)
data[is.na(data)] <- 0

for (d in colnames(data)) data[[d]] <- as.factor(data[[d]])


p1 <- ggtree(tree, size=1.2, layout='slanted') +
    geom_tiplab(align=TRUE, linesize=0, offset=11) +
    scale_x_continuous(
        limits = c(0, 20)
    ) +
    theme_tree()

# add node labels

#nodes <- data.frame(
#    node = c('36', '35', '34', '33', '32', '31', '30', '29'),
#    label = c('Northern', 'Ucayali', 'Southern', 'Poyanawa', 'Marubo', 'Headwaters', 'Central Southern', 'Pano')
#)
#
#
#p1 <- p1 + geom_nodelab(data=nodes, aes(label=label), alpha=.5, color="gray")


# roots
p1 <- gheatmap(p1, data[roots], width=1.5, offset=0, colnames=TRUE, colnames_position="top") +
    scale_fill_manual(
        values=c("#9AADCF", "#1F4576")
    ) + guides(fill="none")
p1 <- p1 + new_scale_fill()

# formatives
p1 <- gheatmap(p1, data[formatives], width=1.5, offset=5, colnames=TRUE, colnames_position="top") +
    scale_fill_manual(
        values=c("#ECA6A0", "#C72A26")
    ) + guides(fill="none")


ggsave('treefigure.png', p1, width=8, height=6)
