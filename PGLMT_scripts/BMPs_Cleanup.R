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

if (!requireNamespace("tidyr", quietly=TRUE)) install.packages("tidyr")
require(tidyr)

if (!requireNamespace("dplyr", quietly=TRUE)) install.packages("dplyr")
require(dplyr)

if (!requireNamespace("stringr", quietly=TRUE)) install.packages("stringr")
require(stringr)

#orient to correct working directory, just to be sure
here::i_am("PGLMT_scripts/BMPs_Cleanup.R")

#Clean up ER Matrix

#turn ER Matrix into object
ERmat <- "C:/Users/AJohnson/Documents/PGLMT/PGLMT_scripts/MatrixRules_FEB2020.xlsx"

#get a list of the sheets in the file
ERmat_sheets <- getSheetNames(ERmat)

#look at the output and choose which excel sheet you want to load

n <- 1 # enter its location in the list (first = 1, second = 2, etc)

ER_mat_table <- read.xlsx(xlsxFile=ERmat, sheet=ERmat_sheets[n], skipEmptyRows=FALSE, rowNames=FALSE)

names(ER_mat_table)

#set which columns containing guild-specific responses to ER activities are the start and stop points for switching from wide to long
first <- "IBAT-Swarming.(IBAT1)"
last <- "Direct.(D_USFWS)"

#switch from long to wide format
ER_mat_tablel <- gather(ER_mat_table, Guild, Response, all_of(first):all_of(last), factor_key=TRUE)
names(ER_mat_tablel)
#list of columns to drop
drops <- c("Major.Category","Secondary.Categories","Tertiary.Categories","Project.Buffer?")
ERtab <- ER_mat_tablel[ , !(names(ER_mat_tablel) %in% drops)]
ERtab <- ERtab[complete.cases(ERtab),] #remove rows w/ missing data, if they are in there

#assign to a unique unit, based on content
DCNR_ERtab <- ERtab
DCNR_ERtab$Agency <- 'DCNR' 

PFBC_ERtab <- ERtab
PFBC_ERtab$Agency <- 'PFBC'

PGC_ERtab <- ERtab
PGC_ERtab$Agency <- 'PGC'

USFWS_ERtab <- ERtab
USFWS_ERtab$Agency <- 'USFWS'

NLEB_IBAT_ERtab <- ERtab
NLEB_IBAT_ERtab$Agency <- 'NLEB-IBAT'

Geology_ERtab <- ERtab
Geology_ERtab$Agency <- 'Geology'

#glue them all together now that they're all in the same format
ER_GuildxAction <- bind_rows(DCNR_ERtab, PFBC_ERtab, PGC_ERtab, USFWS_ERtab, NLEB_IBAT_ERtab, Geology_ERtab)

#pull out the codes in parentheses for the guild groupings, to assign to a separate column
k <- str_extract_all(ER_GuildxAction$Guild, "\\([^()]+\\)") [[1]]
k <- substring(k, 2, nchar(k)-1) #remove parentheses

ER_GuildxAction$Guide_ID <- k


#read in PGC-ER activity crosswalk files
ER_PGC_cw <- read.csv("ER_PGC_Crosswalk.csv")

#switch to long format, and put all the ER codes into one column
ER_PGC <- gather(ER_PGC_cw, rm, ER_Code, ER_Code:ER_Code.6)
ER_PGC <- ER_PGC[complete.cases(ER_PGC),] #remove all rows with mising data 
ER_PGC <- subset(ER_PGC, select = -c(rm))
