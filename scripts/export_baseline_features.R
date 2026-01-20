#!/usr/bin/env Rscript

library(stringr)
library(tidyverse)

args <- commandArgs(trailingOnly = TRUE)
params <- list(
  results_dir = "data/Classifying_Bipartite_Networks/Results",
  metadata = "data/Classifying_Bipartite_Networks/Data/Metadata.csv",
  output = "data/features/baseline_features.csv",
  min_size = 5,
  randomization = "all"
)

for (arg in args) {
  if (startsWith(arg, "--results-dir=")) {
    params$results_dir <- sub("^--results-dir=", "", arg)
  } else if (startsWith(arg, "--metadata=")) {
    params$metadata <- sub("^--metadata=", "", arg)
  } else if (startsWith(arg, "--output=")) {
    params$output <- sub("^--output=", "", arg)
  } else if (startsWith(arg, "--min-size=")) {
    params$min_size <- as.integer(sub("^--min-size=", "", arg))
  } else if (startsWith(arg, "--randomization=")) {
    params$randomization <- sub("^--randomization=", "", arg)
  }
}

column_specs <- cols(
  randomization = col_character(),
  name = col_character(),
  type = col_character(),
  l1 = col_double(), l2 = col_double(), l3 = col_double(),
  ipr1 = col_double(), ipr2 = col_double(), ipr3 = col_double(),
  l1_cm = col_double(), l1_er = col_double(), l1_reg = col_double(),
  l2_mp = col_double(), l3_mp = col_double(),
  l1_lap = col_double(), l2_lap = col_double(), l3_lap = col_double(),
  alg_conn = col_double(),
  clustering_c = col_double(), clustering_r = col_double(),
  deg_assort = col_double(),
  Q = col_double(), N.olap = col_double(), N.temp = col_double(), N.nodf = col_double(),
  H2 = col_double(), H3 = col_double(), H4 = col_double(), H17 = col_double(),
  cent_between = col_double(), cent_close = col_double(), cent_eigen = col_double(),
  diam = col_double(), mean_path_length = col_double(),
  deg_het_row = col_double(), deg_het_col = col_double()
)

result_files <- Sys.glob(file.path(params$results_dir, "*", "*", "*.csv"))
if (length(result_files) == 0) {
  stop(paste("No results files found under", params$results_dir))
}

metadata <- read_csv(params$metadata, col_types = "cccccccccccccidii")

full_results <- result_files %>%
  lapply(read_csv, progress = FALSE, col_types = column_specs) %>%
  bind_rows() %>%
  left_join(metadata, by = c("type", "name")) %>%
  mutate(type_raw = type) %>%
  mutate(type = str_replace_all(type, c("actorcollaboration" = "actor collaboration"))) %>%
  mutate(type = ifelse(type == "ecologicalinteractions", tolower(feature_1), type)) %>%
  filter(nrows >= params$min_size, ncols >= params$min_size)

if (params$randomization != "all") {
  full_results <- full_results %>%
    filter(randomization == params$randomization)
}

dir.create(dirname(params$output), recursive = TRUE, showWarnings = FALSE)
write_csv(full_results, params$output)
cat("Wrote", params$output, "with", nrow(full_results), "rows\n")
