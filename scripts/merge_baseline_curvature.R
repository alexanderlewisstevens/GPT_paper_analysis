#!/usr/bin/env Rscript

library(tidyverse)

args <- commandArgs(trailingOnly = TRUE)
params <- list(
  baseline = "data/features/baseline_features.csv",
  curvature = "data/features/curvature_features.csv",
  output = "data/features/baseline_plus_curvature.csv",
  randomization = "empirical"
)

for (arg in args) {
  if (startsWith(arg, "--baseline=")) {
    params$baseline <- sub("^--baseline=", "", arg)
  } else if (startsWith(arg, "--curvature=")) {
    params$curvature <- sub("^--curvature=", "", arg)
  } else if (startsWith(arg, "--output=")) {
    params$output <- sub("^--output=", "", arg)
  } else if (startsWith(arg, "--randomization=")) {
    params$randomization <- sub("^--randomization=", "", arg)
  }
}

baseline <- read_csv(params$baseline, show_col_types = FALSE)
curvature <- read_csv(params$curvature, show_col_types = FALSE)

if (params$randomization != "all" && "randomization" %in% names(baseline)) {
  baseline <- baseline %>%
    filter(randomization == params$randomization)
}

join_keys <- c("name" = "name")
if ("type_raw" %in% names(baseline) && "type" %in% names(curvature)) {
  join_keys <- c(join_keys, "type_raw" = "type")
}

combined <- baseline %>%
  left_join(curvature, by = join_keys)

missing_curvature <- sum(is.na(combined$orc_mean))
cat("Merged rows:", nrow(combined), "\n")
cat("Rows missing curvature features:", missing_curvature, "\n")

dir.create(dirname(params$output), recursive = TRUE, showWarnings = FALSE)
write_csv(combined, params$output)
cat("Wrote", params$output, "\n")
