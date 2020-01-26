unimpaired <- read.csv("C:/Users/dsx/Dropbox/Code/belleflopt/data/navarro/unimpaired_flows_data.csv")

spreaded <- tidyr::pivot_wider(names_from = "statistic", values_from = "value", data = unimpaired)
spreaded <- dplyr::select(spreaded, -variable)

write.csv(spreaded, "C:/Users/dsx/Dropbox/Code/belleflopt/data/navarro/unimpaired_flows_spreaded.csv")
