import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def save_processed_data(df, output_path):
    """
    Save the processed DataFrame to a new Excel file.
    
    Args:
        df (pandas.DataFrame): Processed DataFrame
        output_path (str): Path for the output Excel file
    """
    try:
        df.to_excel(output_path, index=False)
        print(f"Processed data saved to: {output_path}")
    except Exception as e:
        print(f"Error saving file: {e}")

def calculate_pre_specificity_score(specificity_ratings):
    """
        Calculates a preliminary specificity score for two specificity ratings - if the third reating is not available yet.
        The score is calculated by adding the seperate ratings up.

        Args:
            specificity_ratings (np.Array): 3 separate specificity ratings

        Returns:
            int or str: The calculated final score
    """

    r2 = specificity_ratings[1]
    r3 = specificity_ratings[2]

    if np.all(pd.notna([r2, r3])) and np.all([r2, r3] == np.array([r2, r3]).astype(int)):
        final_score = (r2) + (r3)
    else:
        final_score = ''
    
    return final_score

def calculate_specificity_score(specificity_ratings):
    """
        Calculates a specificity score for three given seperate specificity ratings.
        The score is calculated by adding the seperate ratings up.

        Args:
            specificity_ratings (np.Array): 3 separate specificity ratings

        Returns:
            int or str: The calculated final score
    """

    if np.all(pd.notna(specificity_ratings)) and np.all(specificity_ratings == specificity_ratings.astype(int)):
        r1 = specificity_ratings[0]
        r2 = specificity_ratings[1]
        r3 = specificity_ratings[2]
    
        final_score = (r1) + (r2) + (r3)
    else:
        final_score = ''
    
    return final_score

def add_specificity_score(file_path, sheet_name="Results"):
    """
    Process Excel file and convert P1, P2, P3 understanding values to numerical scores. Only use the rating for 
    "Understanding (self)".
    
    Args:
        file_path (str): Path to the Excel file
        sheet_name (str, optional): Sheet name to read. If None, reads first sheet.
    
    Returns:
        pandas.DataFrame: DataFrame with original data and new P1, P2, P3 columns
    """

    value_mapping = {
        'very well': 2,
        'well': 1,
        'neither well nor poorly': 0,
        'poorly': -1,
        'very poorly': -2
    }

    output_file_path = "csv_files/experts_specificity_rating.xlsx"
    specificity_ratings = np.zeros(3)
    
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None
    
    target_column = "Understanding (self)"
    
    if target_column not in df.columns:
        print(f"Column '{target_column}' not found in the Excel file.")
        print("Available columns:", list(df.columns))
        return None
    
    # Initialize new columns
    df['P1_score_u_self'] = np.nan
    df['P2_score_u_self'] = np.nan
    df['P3_score_u_self'] = np.nan

    # Process each row
    for idx, row in df.iterrows():
        cell_value = row[target_column]
        
        # Skip if cell is empty or NaN
        if pd.isna(cell_value) or cell_value == '':
            df.loc[idx,"Specificity Score"] = ''
            continue
        
        # Split the cell value by comma
        values = [val.strip() for val in str(cell_value).split(',')]
        
        for i, val in enumerate(values):
            if i < 3:  # Only process first 3 values (P1, P2, P3)
                column_name = f'P{i+1}_score_u_self'
                
                # Extract text after "P1:", "P2:", etc.
                val_text = val.split(":", 1)[1].strip() if ":" in val else val.strip()
                
                val_lower = val_text.lower().strip()

                # Map the value or keep as NaN if empty or not found
                if val_lower == '' or val_lower == 'nan':
                    df.loc[idx, column_name] = np.nan
                elif val_lower in value_mapping:
                    df.loc[idx, column_name] = value_mapping[val_lower]
                else:
                    print(f"Warning: Unrecognized value '{val_text}' in row {idx+1}")
                    df.loc[idx, column_name] = np.nan
                
                specificity_ratings[i] = df.loc[idx, column_name]

        # specificity score for all three experts
        val_specificity_score = calculate_specificity_score(specificity_ratings)   
        df.loc[idx, "Specificity Score"] = np.nan if val_specificity_score == '' else val_specificity_score

        # preliminary specificity score for only 2 experts (the results for the third expert is not yet available)
        pre_specificity_score = calculate_pre_specificity_score(specificity_ratings)
        print(pre_specificity_score)
        df.loc[idx, "Pre Specificity Score"] = np.nan if pre_specificity_score == '' else pre_specificity_score
 
    save_processed_data(df, output_file_path)
    
    return df

def consolidate_specificity_ratings(file_path_specificty, file_path_experts_specificty, output_path):
    """
    Merge two Excel files based on 'Paper_title' and append all columns
    from experts_specificity_rating to specificity_rating.
    
    Args:
        file1_path (str): Path to specificity_rating Excel file.
        file2_path (str): Path to experts_specificity_rating Excel file.
        output_path (str): Path to save the merged Excel file.

    Returns:
        merged_df (pd.Dataframe): Results from expert validation, numerical rating from all expert, expeerts' specificity score 
                                    and researchers' specificity score
    """
    
    # Load both Excel files
    specificity_df = pd.read_excel(file_path_specificty)
    experts_df = pd.read_excel(file_path_experts_specificty)
    
    # Merge the two DataFrames on 'Paper_title'
    merged_df = specificity_df.merge(
        experts_df,
        on='Paper_Title',
        how='left',  # Keeps all rows from specificity_rating even if no match
        suffixes=('', '_expert')  # Avoid column name conflicts
    )
    
    # Save the merged result to a new Excel file
    merged_df.to_excel(output_path, index=False)
    print(f"Merged file saved to: {output_path}")

    return merged_df

def specificity_rating_agreement(file_path_specificty):
    """
    Counts how many rows in an Excel file have the same value in 'Rating', 'Specificity Score' as specified in prio documents,
    and computes the agreement percentage (baseline = rows with all 3 values non-empty).
    
    Args:
        file_path_specificty (str): Path to the Excel file.
    
    Returns:
        tuple: (count_agreement, agreement_percentage)
    """
    df = pd.read_excel(file_path_specificty)

    non_empty = df[['Paper_Title', 'Rating', 'Specificity Score']].dropna()
    non_empty = non_empty[(non_empty['Rating'].astype(str).str.strip() != '') &
                          (non_empty['Specificity Score'].astype(str).str.strip() != '')]
    
    # define what counts as agreement between experts (Specificity Score) and researchers (Rating)
    same_values = (((non_empty['Rating'] == 0) & (non_empty['Specificity Score'] >= 2)) |
                  (((non_empty['Rating'] == 1) | (non_empty['Rating'] == -1)) & (non_empty['Specificity Score'] < 2)))
    
    count_agreement = same_values.sum()
    baseline = len(non_empty)

    # Avoid division by zero
    agreement_percentage = (count_agreement / baseline * 100) if baseline > 0 else 0

    print(f"Agreement on {count_agreement} papers out of {baseline} ({agreement_percentage:.2f}%).")

    paper_titles = non_empty.loc[same_values, 'Paper_Title'].tolist()

    return paper_titles

def match_paper_info(dataframe, excel_file_path, sheet_name=None):
    """
    Matches the paper info with the results of the expert validation. The paper info needs to be combined with the results of 
    the expert validation, such as "Level of detail". This info explains, if the intro text of the selected papers needs
    more or less information to be understandable.
    
    Parameters:
    -----------
    dataframe : pd.DataFrame
        The DataFrame to be updated containing the selected papers with 100% agreement and with the original paper info.
    excel_file_path : str
        Path to the Excel file containing the results of the expert validation
    sheet_name : str or None
        Sheet name to read from Excel file (None for first sheet)
    
    Returns:
    --------
    pd.DataFrame
        Updated DataFrame with filled columns
    """
    excel_data = pd.read_excel(excel_file_path, sheet_name=0)
    columns_to_fill = ['Level of detail', 'Additional info', 'Distracting info', 'Comments', 'Specificity Score']
    updated_df = dataframe.copy()
    
    # Create mapping
    excel_mapping = {}
    for _, row in excel_data.iterrows():
        paper_title = row['Paper_Title']
        if pd.notna(paper_title):
            excel_mapping[paper_title] = {col: row[col] for col in columns_to_fill if col in excel_data.columns}
    
    # Fill only empty cells
    matches_found = 0
    for idx, row in updated_df.iterrows():
        paper_name = row['Paper Name']
        if pd.notna(paper_name) and paper_name in excel_mapping:
            for col in columns_to_fill:
                if col in updated_df.columns and col in excel_mapping[paper_name]:
                    # Only fill if current cell is empty/null
                    if pd.isna(updated_df.at[idx, col]) or updated_df.at[idx, col] == '':
                        # Check if we're about to assign a string to a numeric column to prevent assigning string values to a column pandas has inferred as float64
                        if (isinstance(excel_mapping[paper_name][col], str) and 
                            updated_df[col].dtype in ['float64', 'int64']):
                            updated_df[col] = updated_df[col].astype('object')
                        
                        updated_df.at[idx, col] = excel_mapping[paper_name][col]
            matches_found += 1

    return updated_df

def get_agreed_papers(input_file_path, final_list_papers, file_specificity_comparison):
    """
    Filters an Excel file to keep only rows where 'Paper Name' column values 
    match values in final_list_papers, then saves to a new Excel file.
    
    Args:
        input_file_path (str): Path to excel file containing all papers used in the expert validation.
        final_list_papers (list): List of paper names to match against
        file_specificity_comparison (str, optional): Path for the file containing the results of the expert validation.                                
    
    Returns: 
        final_papers_df (pd.DataFrame): Papers with 100% agreement on the specificity score between researchers and experts
             
    Raises:
        FileNotFoundError: If input file doesn't exist
        KeyError: If 'Paper Name' column doesn't exist in the Excel file
        Exception: For other pandas/file operation errors
    """
    output_file_path = "csv_files/final_papers_agreed.xlsx"

    try:
        # Check if input file exists
        if not os.path.exists(input_file_path):
            raise FileNotFoundError(f"Input file not found: {input_file_path}")
        
        df = pd.read_excel(input_file_path)
        
        # Check if 'Paper Name' column exists
        if 'Paper Name' not in df.columns:
            raise KeyError("Column 'Paper Name' not found in the Excel file. Available columns: " + 
                          ", ".join(df.columns.tolist()))
        
        # Convert final_list_papers to set for faster lookup
        paper_names_set = set(final_list_papers)
        
        filtered_df = df[df['Paper Name'].isin(paper_names_set)]
        print(f"Found {len(filtered_df)} matching rows out of {len(df)} total rows")   

        final_papers_df = match_paper_info(filtered_df, file_specificity_comparison)
        
        final_papers_df.to_excel(output_file_path, index=False)
        
        print(f"\nSuccessfully created Excel file containing papers with 100% agreement on their specificity: {output_file_path}")

        return final_papers_df
        
    except Exception as e:
        print(f"Error processing Excel file: {str(e)}")
        raise

def get_non_specific_papers(input_df):
    # get all papers that have a Specificity Score thats >= 2 and the researchers'rating = 0
    """
    Filters an Excel file to keep only rows where 'Specificity Score' column values are >= 2 (i.e. non specific papers).
    
    Args:
        input_df (pd.Dataframe): All papers with 100% agreement between researchers and experst regarding their specificity.                              
    
    Returns: - 
             
    Raises:
        FileNotFoundError: If input file doesn't exist
    """
    output_file_path = "csv_files/final_papers_non_specific.xlsx"

    try:               
        if 'Validation Nerd Factor' not in input_df.columns:
            raise KeyError("Column 'Validation Nerd Factor' not found in the Excel file. Available columns: " + 
                          ", ".join(input_df.columns.tolist()))
        
        # get papers with researchers' rating == 0 (the input papers are only paper that match regarding the reserachers' and experts rating)
        filtered_df = input_df[(input_df["Validation Nerd Factor"] == 0)]
        print(f"Found {len(filtered_df)} matching rows for non specific papers out of {len(input_df)} total rows (researchers' and experts' rating)")   
        
       # TO-DO: irerate through the column "Level of detail" an quantify the rating

        
        # Save filtered dataframe to new Excel file       
        save_processed_data(filtered_df, output_file_path)
        
        print(f"\nSuccessfully created filtered Excel file containing the non specific papers: {output_file_path}")

        return filtered_df
        
    except Exception as e:
        print(f"Error processing Excel file: {str(e)}")
        raise

def calculate_agreement(df, threshold):
    """
    Calculate agreement percentage for a given threshold.
    
    Agreement exists when:
    1. Specificity Score >= threshold AND Rating = 0
    2. Specificity Score < threshold AND Rating = 1 or -1
    
    Args:
        df: DataFrame with 'Specificity Score' and 'Rating' columns
        threshold: Threshold value to test
    
    Returns:
        Agreement percentage (0-100)
    """
    # Filter out rows with empty/null values
    valid_df = df.dropna(subset=['Specificity Score', 'Rating'])
    
    if len(valid_df) == 0:
        return 0
    
    # Count agreements based on the two cases
    case1 = (valid_df['Specificity Score'] >= threshold) & (valid_df['Rating'] == 0)
    case2 = (valid_df['Specificity Score'] < threshold) & ((valid_df['Rating'] == 1) | (valid_df['Rating'] == -1))
    
    agreements = case1 | case2
    agreement_count = agreements.sum()
    
    # Calculate percentage
    agreement_percentage = (agreement_count / len(valid_df)) * 100
    
    return agreement_percentage

def analyze_agreement_threshold(df, threshold_range=(-6, 6), step=1):
    """
    Derive threshold for the acceptance of papers by analyzing the agreement between researchers and experts with varying thresholds.

    Args:
        df: DataFrame with 'Specificity Score' (experts' rating) and 'Rating' (researchers' rating) columns
        threshold_range: Tuple of (min_threshold, max_threshold)
        step: Step size for threshold increments
    """
    try:
        output_path = 'csv_files/treshold_analysis.xlsx'

        # Generate threshold values
        thresholds = np.arange(threshold_range[0], threshold_range[1] + step, step)
        
        # Calculate agreement for each threshold
        agreements = []
        print(f"\nAgreement percentages for each threshold:")
        print(f"{'Threshold':<10} {'Agreement %':<12}")
        print("-" * 22)
        
        for threshold in thresholds:
            agreement_pct = calculate_agreement(df, threshold)
            agreements.append(agreement_pct)
            print(f"{threshold:<10.1f} {agreement_pct:<12.2f}")
        
        print("-" * 22)
        
        # Prepare results dataframe
        results_df = pd.DataFrame({
            'Threshold': thresholds,
            'Agreement_Percentage': agreements
        })
        
        # Set Seaborn style
        sns.set(style="whitegrid", context="talk")
        
        # Plot Agreement Percentage vs Threshold
        plt.figure(figsize=(12, 8))
        sns.lineplot(
            x='Threshold', 
            y='Agreement_Percentage', 
            data=results_df, 
            marker='o', 
            linewidth=2
        )
        plt.xlabel('Threshold')
        plt.ylabel('Agreement (%)')
        plt.title('Agreement Analysis: Agreement Percentage for each Threshold (#56)', fontsize=14, fontweight='bold')
        plt.xlim(threshold_range)
        plt.ylim(0, 100)
        plt.xticks(range(threshold_range[0], threshold_range[1] + 1))
        plt.yticks(range(0, 101, 10))
        plt.grid(True, alpha=0.3)
        plt.show()
        
        # Print dataset statistics
        valid_df = df.dropna(subset=['Specificity Score', 'Rating'])
        total_rows = len(df)
        valid_rows = len(valid_df)
        skipped_rows = total_rows - valid_rows
        
        print(f"\nDataset Statistics:")
        print(f"Total rows: {total_rows}")
        print(f"Valid rows (no missing values): {valid_rows}")
        print(f"Skipped rows (with missing values): {skipped_rows}")
        print(f"Rating distribution:")
        print(valid_df['Rating'].value_counts().sort_index())
        
        # Save results
        save_processed_data(results_df, output_path)

        return results_df
    
    except Exception as e:
        print(f"Error in analyze_agreement_threshold function: {str(e)}")

def pre_analyze_agreement_threshold(df, threshold_range=(-4, 4), step=1):
    """
    Derive threshold for the acceptance of papers by analyzing the agreement between researchers and experts 
    with varying thresholds for only two of the three experts (if the results for the third expert is not available yet).

    Args:
        df: DataFrame with 'Pre Specificity Score' (experts' rating) and 'Rating' (researchers' rating) columns
        threshold_range: Tuple of (min_threshold, max_threshold)
        step: Step size for threshold increments
    """
    try:
        output_path = 'csv_files/treshold_analysis.xlsx'

        # Generate threshold values
        thresholds = np.arange(threshold_range[0], threshold_range[1] + step, step)
        
        # Calculate agreement for each threshold
        agreements = []
        print(f"\nAgreement percentages for each threshold:")
        print(f"{'Threshold':<10} {'Agreement %':<12}")
        print("-" * 22)
        
        for threshold in thresholds:
            agreement_pct = calculate_agreement(df, threshold)
            agreements.append(agreement_pct)
            print(f"{threshold:<10.1f} {agreement_pct:<12.2f}")
        
        print("-" * 22)
        
        # Prepare results dataframe
        results_df = pd.DataFrame({
            'Threshold': thresholds,
            'Agreement_Percentage': agreements
        })
        
        # Set Seaborn style
        sns.set(style="whitegrid", context="talk")
        
        # Plot Agreement Percentage vs Threshold
        plt.figure(figsize=(12, 8))
        sns.lineplot(
            x='Threshold', 
            y='Agreement_Percentage', 
            data=results_df, 
            marker='o', 
            linewidth=2
        )
        plt.xlabel('Threshold')
        plt.ylabel('Agreement (%)')
        plt.title('Agreement Analysis: Agreement Percentage for each Threshold (#56)', fontsize=14, fontweight='bold')
        plt.xlim(threshold_range)
        plt.ylim(0, 100)
        plt.xticks(range(threshold_range[0], threshold_range[1] + 1))
        plt.yticks(range(0, 101, 10))
        plt.grid(True, alpha=0.3)
        plt.show()
        
        # Print dataset statistics
        valid_df = df.dropna(subset=['Pre Specificity Score', 'Rating'])
        total_rows = len(df)
        valid_rows = len(valid_df)
        skipped_rows = total_rows - valid_rows
        
        print(f"\nDataset Statistics:")
        print(f"Total rows: {total_rows}")
        print(f"Valid rows (no missing values): {valid_rows}")
        print(f"Skipped rows (with missing values): {skipped_rows}")
        print(f"Rating distribution:")
        print(valid_df['Rating'].value_counts().sort_index())
        
        # Save results
        save_processed_data(results_df, output_path)

        return results_df
    
    except Exception as e:
        print(f"Error in pre_analyze_agreement_threshold function: {str(e)}")

def analyze_individual_expert(df):
    """
    Plot the number of occurrences for each value in the columns containing the specificity raitings for each expert.
    Each column is represented as a separate colored line on the same plot.
    """
    try:
        label_mapping = {
            'P1_score_u_self': 'Expert 1',
            'P2_score_u_self': 'Expert 2',
            'P3_score_u_self': 'Expert 3'
        }

        # columns to analyze
        columns = ['P1_score_u_self', 'P2_score_u_self', 'P3_score_u_self']
        
        # Prepare data for plotting
        plot_data = pd.DataFrame()
        
        for col in columns:
            counts = df[col].value_counts().sort_index()
            temp_df = pd.DataFrame({
                'Value': counts.index,
                'Count': counts.values,
                'Column': col
            })
            plot_data = pd.concat([plot_data, temp_df], ignore_index=True)
        
        # Set Seaborn style
        sns.set_theme(style="whitegrid", context="talk")

        # Replace the 'Column' values in plot_data
        plot_data['Column'] = plot_data['Column'].map(label_mapping)
        
        # Plot lineplot
        plt.figure(figsize=(12, 8))
        sns.lineplot(
            x='Value', 
            y='Count', 
            hue='Column', 
            data=plot_data, 
            marker='o', 
            linewidth=2
        )
        plt.xlabel('Specificity Rating (-2 = too specific; 2 = very clear)')
        plt.ylabel('Number of Occurrences')
        plt.title('Rating Tendency of Experts', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend(title='Experts', loc='upper left')
        
        # Set x-axis ticks to integers from -2 to 2
        plt.xticks(range(-2, 3))
        
        plt.show()
    
    except Exception as e:
        print(f"Error in plot_value_counts function: {str(e)}")

if __name__ == "__main__":
    input_file_path = "csv_files/results_experts_consolidated.xlsx" # all results from all experts in one file
    file_path_researchers_specificity = "csv_files/researchers_specificity_rating.xlsx" # researchers' specificity rating
    file_path_experts_specificty = "csv_files/experts_specificity_rating.xlsx"  # experts' specificity rating
    file_path_specificity_consolidated = "csv_files/specificity_rating_consolidated.xlsx"   # ratings from both experts and researchers in one file
    all_sampled_papers = "csv_files/all_sampled_papers.xlsx"    # all papers sampled for the expert validation

    # calculate and check which papers are labeled as too specific by experts
    df = add_specificity_score(input_file_path)
    
    #calculate the agreement of the specificity rating for experts and researchers
    specificity_researchers_experts_df = consolidate_specificity_ratings(file_path_researchers_specificity, file_path_experts_specificty, file_path_specificity_consolidated)
    
    # Calculate agreement on specificty rating between researchers and experts
    papers_agreed_list = specificity_rating_agreement(file_path_specificity_consolidated) # list of papers titles with 100% agreement
    papers_agreed_df = get_agreed_papers(all_sampled_papers, papers_agreed_list, file_path_specificity_consolidated)

    # get final set of papers that are not too specific according to experts and researchers
    papers_non_specific_df = get_non_specific_papers(papers_agreed_df)

    # plot the ratings (researchers and expert(s))
    #agreement_analysis = analyze_agreement_threshold(specificity_researchers_experts_df)
    #pre_analyze_agreement_threshold(specificity_researchers_experts_df)

    analyze_individual_expert(specificity_researchers_experts_df)



