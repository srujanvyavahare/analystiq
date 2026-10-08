import pytest
import pandas as pd
from core.pipeline import run_analysis_pipeline
from unittest.mock import patch

@patch('core.pipeline.get_insights_and_code')
@patch('core.pipeline.execute_code')
def test_confidence_green(mock_execute, mock_llm):
    # Setup mock returns
    mock_llm.return_value = {
        'python_code': 'result_df = df.head(100)',
        'insights': ['test'],
        'assumptions': {}
    }
    
    # Return 100 rows, matching the input 100 rows
    mock_df = pd.DataFrame({'a': range(100)})
    mock_execute.return_value = {
        'success': True,
        'locals': {'result_df': mock_df, 'fig': None}
    }
    
    result = run_analysis_pipeline("test", mock_df, "info")
    assert result['confidence'] == "Green"

@patch('core.pipeline.get_insights_and_code')
@patch('core.pipeline.execute_code')
def test_confidence_red_small_sample(mock_execute, mock_llm):
    mock_llm.return_value = {
        'python_code': 'result_df = df.head(10)',
        'insights': ['test'],
        'assumptions': {}
    }
    
    # Return < 30 rows
    mock_df = pd.DataFrame({'a': range(10)})
    mock_execute.return_value = {
        'success': True,
        'locals': {'result_df': mock_df, 'fig': None}
    }
    
    # Pass in a large dataframe (100) so it's a sample drop
    result = run_analysis_pipeline("test", pd.DataFrame({'a': range(100)}), "info")
    assert result['confidence'] == "Red"
    assert any("small sample" in r for r in result['confidence_reason'])

@patch('core.pipeline.get_insights_and_code')
@patch('core.pipeline.execute_code')
def test_confidence_amber_inferred(mock_execute, mock_llm):
    mock_llm.return_value = {
        'python_code': 'result_df = df',
        'insights': ['test'],
        'assumptions': {'inferred_mapping': {'rev': 'Revenue'}}
    }
    
    mock_df = pd.DataFrame({'a': range(100)})
    mock_execute.return_value = {
        'success': True,
        'locals': {'result_df': mock_df, 'fig': None}
    }
    
    result = run_analysis_pipeline("test", mock_df, "info")
    assert result['confidence'] == "Amber"
    assert any("Inferred column mappings" in r for r in result['confidence_reason'])
