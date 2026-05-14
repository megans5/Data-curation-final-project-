import pandas as pd
import json
import matplotlib.pyplot as plt
import CurationLogger

def load_dataset(config_path):
    with open(config_path, "r") as file_name:
        config = json.load(file_name)
    
    # get the file path and columns to be included from config file
    file_path = config.get("filePath")
    column_names = config.get("columnNames")
    type_by_col = config.get("typeByCol")
    quality_check_col = config.get("qualityCheckCol")
    null_vals = config.get("nullVals")  
    id_col = config.get("idCol")
    data_name = config.get("dataName")
    null_allowed_cols = config.get("nullAllowedCols") or []

    # create a dataframe from the csv using only the specified columns
    df = pd.read_csv(file_path, encoding="utf-8", usecols=column_names)

    return df, type_by_col, quality_check_col, null_vals, id_col, data_name, null_allowed_cols

def quality_check(df, quality_check_col, logger, removal_dict):
    logger.step("Quality check", "If a quality column is provided, remove rows which failed that check")
    rows_removed_total = 0
    if quality_check_col:
        # iterate through all of the quality check column items 
        for column_name, values in quality_check_col.items():
            # log the current number of rows in the df
            num_rows_before = len(df)
            logger.log(f"\tFor quality check column {column_name}: \n\t\t\tBefore removal number of rows: {num_rows_before}")
            
            if isinstance(values, list):
                # remove all rows of the df if the value of the quality check item is equal to any of the values provided for indicating poor quality
                df = df[~df[column_name].isin(values)]
            else:
                df = df[~df[column_name].eq(values)]
            
            # log the new number of rows and the number of rows removed 
            num_rows_after = len(df)
            logger.log(f"\t\tAfter removal number of rows: {num_rows_after}")
            logger.log(f"\t\tTotal number of rows removed: {num_rows_before - num_rows_after}")
            rows_removed_total = rows_removed_total + (num_rows_before - num_rows_after)
    else:
        logger.log("There is no quality check column.")

    # add the total number of rows removed to the dictionary
    removal_dict['Quality Check'] = rows_removed_total
    return df, removal_dict

def remove_null(df, null_vals, logger, removal_dict, null_allowed_cols):
    logger.step("Remove null", "Remove all null values")
    rows_removed_total = 0
    for column_name in [col for col in df.columns if col not in null_allowed_cols]:
        num_rows_before = len(df)
        # remove all rows with actually null variables
        df = df[~df[column_name].isna()]

        # remove all rows which are empty strings
        df = df[~df[column_name].astype(str).eq("")]
        
        # if there's a specific string or list of strings that means null, remove it
        if null_vals:
            if isinstance(null_vals, list):
                for null_val in null_vals:
                    df = df[~((df[column_name]).astype(str).str.lower().str.contains(null_val))]
            else:
                df = df[~((df[column_name]).astype(str).str.lower().str.contains(null_vals))]
        num_rows_after = len(df)
       # log number of rows removed
        difference = num_rows_before - num_rows_after
        if difference > 0:
            logger.log(f"\tFor null removal on column {column_name}: \n\t\t\tBefore removal number of rows: {num_rows_before}")
            logger.log(f"\t\tAfter removal number of rows: {num_rows_after}")
            logger.log(f"\t\tTotal number of rows removed: {num_rows_before - num_rows_after}")
            # add number of rows removed to the tracker of rows removed
            rows_removed_total = rows_removed_total + (num_rows_before - num_rows_after)
        
    logger.log(f"Total number of rows removed: {rows_removed_total}")
    # add the total number of rows removed to the dictionary
    removal_dict['Remove Null Values'] = rows_removed_total
    return df, removal_dict

def remove_duplicates(df, id_col, logger, removal_dict):
    logger.step("Remove duplicate values", f"Remove all duplicate values based on the {id_col} column")
    num_rows_before = len(df)
    logger.log(f"\tBefore removal of duplicates: {num_rows_before} rows")
    
    # get rid of any rows that have the same id column (which should be unique)
    df = df.drop_duplicates(subset=id_col)
    logger.log(f"\tAfter removal of duplicates: {len(df)} rows")
    logger.log(f"\tTotal number of rows removed: {num_rows_before - len(df)}")
    # add the total number of rows removed to the dictionary
    removal_dict['Remove Duplicates'] = num_rows_before - len(df)
    return df, removal_dict
    

def correct_types(df, type_by_col, logger, removal_dict):

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
    # add the total number of rows removed to the dictionary
    removal_dict['Remove Out of Range'] = rows_removed_total
    return df, removal_dict

def plot_graphs(df, removal_dict):
    # turn the dict into df so it can be plotted and rename columns for graph 
    removal_df = pd.DataFrame(list(removal_dict.items()), columns = ["Curation Step", "Number of Rows Removed"])
    removal_df.plot.bar(x="Curation Step", y="Number of Rows Removed", color=None)
    
    # plot rows removed by curation step
    plt.ylabel("Number of Rows Removed")
    plt.xlabel("Curation Step")
    plt.title("Rows Removed by Curation Step")
    plt.xticks(rotation=13, ha='right')
    plt.savefig("output/removal_bar_graph.png")


def main():
    logger = CurationLogger.CurationLogger("output/curation_log.txt")
    logger.step("Begin Curation")
    
    # to change which data set is used, either use "config_cces.json" or "config_anes.json"
    df, type_by_cols, quality_check_col, null_val, id_col, data_name, null_allowed_cols = load_dataset("config_anes.json")
    df.to_csv(f"data/raw_{data_name}_data.csv", index=False)
    removal_dict = {}
    num_rows_before = len(df)
    df, removal_dict = quality_check(df, quality_check_col, logger, removal_dict)
    df, removal_dict = remove_duplicates(df, id_col, logger, removal_dict)
    df, removal_dict = remove_null(df, null_val, logger, removal_dict, null_allowed_cols)
    df, removal_dict = correct_types(df, type_by_cols, logger, removal_dict)

    df.to_csv(f"data/curated_{data_name}_data.csv", index=False)

    plot_graphs(df, removal_dict)
    logger.step("Report", f"Before curation, the data had {num_rows_before} rows. After curtion, it has {len(df)} rows. {num_rows_before - len(df)} rows were removed.")
    logger.close()

main()