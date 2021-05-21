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

#################################################################################
################################################################################

#########################
#1. Clean up ER Matrix ##
#########################

################################################################################
################################################################################

##########################################################
#1a. extract and format sp x code sheets for each agency #
##########################################################

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
#the problems are for "A" and "S', the NLEB ones, "Within.Bog.Turtle,.but.outside.known.watershed", and geology--those have to be fixed by hand either prior to reading in, or post-hoc

#export finished file for future reference/so you don't have to rebuild it until it gets updated
#write.csv(ER_GuildxAction, file="ER_GuildxAction_long.csv")
#read back in file now that it has been slighly hand cleaned (fixed the guild codes that didn't work with parentheses)


ER_GuildxAction <- read.csv(file="ER_GuildxAction_long.csv")

#also some of the matrix cells have a comma separating multiple responses, need to address
ER_GuildxAction2 <- ER_GuildxAction %>% separate(Response, c("R1","R2"), sep = "([,])")

#reformat back into long, and then remove missing data rows
ER_GuildxAction2 <- gather(ER_GuildxAction2, temp, Response, R1:R2)
ER_GuildxAction2 <- ER_GuildxAction2[complete.cases(ER_GuildxAction2),] #remove rows w/ missing data, if they are in there

#remove unnecessary columns
drops <- c("X","temp")
ER_GuildxAction2 <- ER_GuildxAction2[ , !(names(ER_GuildxAction2) %in% drops)]
names(ER_GuildxAction2)[1] <- "ER_Code" #rename ER Code column
#write further cleaned .csv file to store
write.csv(ER_GuildxAction2, file="ER_GuildxAction_formatted.csv")

#############################################################
#1b. extract and reformat the further questions spreadsheet #
#############################################################

#reformat the further questions spreadsheet
ERmat_sheets
n <- 8 # enter its location in the list (for Avoidance Measures)
#this one had to have some manual edits made to it, because some of the questions had follow-up questions, but they weren't set up in a way that allowed easy automatic extraction.
#Created two new columns--one which attributed each follow up level to the original question, and one which indicated whether the question had a set of follow-up questions

ER_mat_table <- read.xlsx(xlsxFile=ERmat, sheet=ERmat_sheets[n], skipEmptyRows=FALSE, rowNames=FALSE)

names(ER_mat_table)

#select out just the main question text (not the follow-up sub-questions)

ER_Q_main <- subset(ER_mat_table, ER_mat_table$Follow_up %in% c("Y", "N"))

ER_Q_sub <- subset(ER_mat_table, ER_mat_table$Follow_up =="sub")

#convert from wide to long
ER_Q_main <- gather(ER_Q_main, Q_Response, BMP, Yes:Unknown, factor_key=TRUE)
ER_Q_main <- ER_Q_main[complete.cases(ER_Q_main),] #remove rows w/ missing data as a result of missing Q cases

ER_Q_sub <- gather(ER_Q_sub, Q_Response, BMP, Yes:Unknown, factor_key=TRUE)
ER_Q_sub <- ER_Q_sub[complete.cases(ER_Q_sub),] 

write.csv(ER_Q_main, file="ER_Questions_main.csv") #write out the result
write.csv(ER_Q_sub, file="ER_Questions_sub.csv") #write out the result

################################################
#1c. extract and reformat the BMP spreadsheets #
################################################

#create long-formatted spreadsheets with the Conservation Measures, Avoidance Measures, and responses to questions

#get a list of the sheets in the ER matrix file
ERmat_sheets

#look at the output and choose which excel sheet you want to load

n <- 9 # enter its location in the list (for Avoidance Measures)

ER_mat_table <- read.xlsx(xlsxFile=ERmat, sheet=ERmat_sheets[n], skipEmptyRows=FALSE, rowNames=FALSE)

head(ER_mat_table)

AvoidanceMeasures <- ER_mat_table
names(AvoidanceMeasures) <- c("ER_BMP_Code","TargetGuilds","Text") #rename columns

n <- 10 # enter its location in the list (for Conservation Measures)

ER_mat_table <- read.xlsx(xlsxFile=ERmat, sheet=ERmat_sheets[n], skipEmptyRows=FALSE, rowNames=FALSE)
ConservationMeasures <- ER_mat_table
names(ConservationMeasures) <- c("ER_BMP_Code","TargetGuilds","Text")

n <- 11 # enter its location in the list (for Conservation Measures)

ER_mat_table <- read.xlsx(xlsxFile=ERmat, sheet=ERmat_sheets[n], skipEmptyRows=FALSE, rowNames=FALSE)
InformationRequest <- ER_mat_table
names(InformationRequest) <- c("ER_BMP_Code","TargetGuilds","Text")

#glue them all together--first create list of df so that the name of each individual BMP table can be incorporated into big table as a factor
BMPs <- list(AvoidanceMeasures, ConservationMeasures, InformationRequest)
names(BMPs) <-c("AvoidanceMeasures", "ConservationMeasures", "InformationRequest")

ER_BMPs_bycode <- bind_rows(BMPs, .id="BMP_type")
names(ER_BMPs_bycode)

#export result for future ref
write.csv(ER_BMPs_bycode, file="ER_BMPs_bycode.csv")

############################################################################################
############################################################################################

########################################
## 2. Clean up PGC-ER crosswalk files ##
########################################

###########################################################################################

#read in PGC-ER activity crosswalk files
ER_PGC_cw <- read.csv("ER_PGC_Crosswalk.csv")

#switch to long format, and put all the ER codes into one column
ER_PGC <- gather(ER_PGC_cw, rm, ER_Code, ER_Code:ER_Code.6)
ER_PGC <- ER_PGC[complete.cases(ER_PGC),] #remove all rows with mising data 
ER_PGC <- subset(ER_PGC, select = -c(rm))
