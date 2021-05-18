#-------------------------------------------------------------------------------
# Name:        BMPs_Cleanup.r
# Purpose:     Clean up and format the BMP and activity category spreadsheets for the PGLMT.
# Author:      Anna Johnson
# Created:     2021-05-18
# Updated:     
#
# Updates:
#
# To Do List/Future ideas:
#
#-------------------------------------------------------------------------------
#load required packages
if (!requireNamespace("here", quietly=TRUE)) install.packages("here")
require(here)

if (!requireNamespace("openxlsx", quietly=TRUE)) install.packages("openxlsx")
require(openxlsx)

#orient to correct working directory, just to be sure
here::i_am("PGLMT_scripts/BMPs_Cleanup.R")

#Clean up ER Matrix

#turn ER Matrix into object
ERmat <- "C:/Users/AJohnson/Documents/PGLMT/PGLMT_scripts/MatrixRules_FEB2020.xlsx"

#get a list of the sheets in the file
ERmat_sheets <- getSheetNames(ERmat)

#look at the output and choose which excel sheet you want to load

n <- 4 # enter its location in the list (first = 1, second = 2, etc)
ER_mat_table <- read.xlsx(xlsxFile=ERmat, sheet=ERmat_sheets[n], skipEmptyRows=FALSE, rowNames=FALSE)
names(ER_mat_table)
