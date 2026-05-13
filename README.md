# Data-curation-final-project-
WHAT THE PROJECT DOES:
    - This project cleans survey data sets. It uses a csv file and a config file in order to automatically clean and curate data.
    Steps:
    1. Install dependencies:
    
    pandas, json, and matplotlib are required to run this project. Run the following commands to install them.

    pip install pandas
    pip install json
    pip install matplotlib


    2. Edit config file for your data set.
        - The config file requires the user to provide the path, file path, and file name in order to read in the csv.
        - dataName is for a shorted version of the name of the data used to name output
        - "columnNames" should be a list of columns the user wants to be read in from the csv
        -  "typeByCol" should include the type of each column (if known) and range of that column (if known)
        - "idCol" is the column that is used to check for duplicates
        -  "qualityCheckCol" should be the column that is used to check the quality of the data and the value which means the row should be dropped 
        - "nullVals" is a list of the string values that mean null for that dataset 
        - "nullAllowedCols" is a list of columns which are allowed to be null, since in surveys there are sometimes followup questions to previously asked questions, meaning that if someone answered no to a question, they will not be asked the followup, meaning their answers for the followup questions would be null. Thus, we don't want to remove null values for those columns
    3. In main, change the load_dataset line to load in the name of your config file
    
    4. Run the following command in your terminal: 
        python src.py 
        
        Steps automatically taken after running src file:
            - Rows which fail the quality check of the quality column are removed
            - duplicate values based on the idCol are removed
            - all null values, excluding those from the nullAllowedCols, are removed
            - columns' types are corrected if they do not match the type listed in the config file
            - the range of values for all columns are checked and rows are deleted if they fall outside of that range
        
        Output:
            - All of these steps are logged in the curation_log.txt file, with the step number and the number of rows deleted.
            - A removal_bar_graph.png file is created, which is a bar graph showing the number of rows removed for each curation step.
            -  raw_dataName_data.csv and curated_dataName_data.csv files are created

    Assumptions:
        - assumes input file is a csv
        - assumes user knows the types of columns
        - assumes user knows the name of null values
    
    Limitations:
        - does not work for non csv files



