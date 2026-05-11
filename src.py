import pandas as pd
import json
# import numpy as np
import CurationLogger

def load_dataset(config_path):
    with open(config_path, "r") as file_name:
        config = json.load(file_name)
    
    # get the file path and columns to be included from config file
    file_path = config.get("file_path")
    column_names = config.get("columnNames")
    type_by_col = config.get("typeByCol")
    quality_check_col = config.get("qualityCheckCol")

    # create a dataframe from the csv using only the specified columns
    df = pd.read_csv(file_path, encoding="cp1252", usecols=column_names)

    return df, type_by_col, quality_check_col

def quality_check(df, quality_check_col, logger):
    logger.step("Quality check", "If a quality column is provided, remove rows which failed that check")
    if quality_check_col:
        # iterate through all of the quality check column items 
        for column_name, values in quality_check_col.items():
            # log the current number of rows in the df
            num_rows_before = len(df)
            logger.log(f"\tFor quality check column {column_name}: \n\t\t\tBefore removal number of rows: {num_rows_before}")
            # remove all rows of the df if the value of the quality check item is equal to any of the values provided for indicating poor quality
            df = df[~df[column_name].isin(values)]
            # log the new number of rows and the number of rows removed 
            num_rows_after = len(df)
            logger.log(f"\t\tAfter removal number of rows: {num_rows_after}")
            logger.log(f"\t\tTotal number of rows removed: {num_rows_before - num_rows_after}")
    else:
        logger.log("There is no quality check column.")

    return df

def correct_types(df, type_by_col, logger):

    logger.step("Type Correction and Range Checking", "Check the type of each column and " \
    "correct it if inconsistent with type from config. Remove any rows with values outside of range specified")

    rows_removed_total = 0
    # iterate through the specified type information for each column from config
    for column_name, type_info in type_by_col.items():
        # check if range is included in the info
        if isinstance(type_info, list):
            col_type = type_info[0]
            lower_range = type_info[1]
            upper_range = type_info[2]
        else:
            col_type = type_info
            lower_range = None
            upper_range = None
        
        # If the current data type of the column does not match what it should be and it should be a date (special case)
        if df[column_name].dtype != col_type and col_type == "datetime64[us]":
            try:
                old_type = df[column_name].dtype
                # convert the column to datetime type
                df[column_name] = pd.to_datetime(df[column_name], errors="coerce")
                logger.change(column_name, "Type: " + str(old_type), str(df[column_name].dtype))
             # log an error if conversion cannot be made
            except Exception as e:
                logger.error(column_name, f"could not convert from {str(old_type)} to {col_type}")
        # If the current data type of the column does not match what it should be and it shouldn't be a date
        elif df[column_name].dtype != col_type:
            try:
                old_type = df[column_name].dtype
                # convert the column to whatever is specified by the config
                df[column_name] = df[column_name].astype(col_type)
                logger.change(column_name, "Type: " + str(old_type), col_type)
            # log an error if conversion cannot be made
            except Exception as e:
                logger.error(column_name, f"could not convert from {str(old_type)} to {col_type}")
        if lower_range and upper_range:
            num_rows_before = len(df)
            
            # remove any rows that have values below the lower range or above upper range 
            df = df[~(df[column_name]<lower_range)] 
            df = df[~(df[column_name]>upper_range)] 
            
            # log the new number of rows and the number of rows removed if any rows were removed
            num_rows_after = len(df)
            difference = num_rows_before - num_rows_after
            if difference > 0:
                logger.log(f"\tFor range check column {column_name}: \n\t\t\tBefore removal number of rows: {num_rows_before}")
                logger.log(f"\t\tAfter removal number of rows: {num_rows_after}")
                logger.log(f"\t\tTotal number of rows removed: {num_rows_before - num_rows_after}")
                # add number of rows removed to the tracker of rows removed
                rows_removed_total = rows_removed_total + (num_rows_before - num_rows_after)
        
    logger.log(f"Total number of rows removed for entire range check: {rows_removed_total}")
    return df


def main():
    logger = CurationLogger.CurationLogger("curation_log.txt")
    logger.step("Begin Curation")
    df, type_by_cols, quality_check_col = load_dataset("config.json")

    print(df.shape)
    for col in df.columns:
        print(col + "  ")
    df = quality_check(df, quality_check_col, logger)
    df = correct_types(df, type_by_cols, logger)


    logger.close()

main()