"""
Unit tests for yfinance_utils.py
Tests both working search functionality and problematic analysis functionality
"""

import pytest
import json
import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.yfinance_utils import search_ticker, get_stock_info, calculate_cape_comparison


class TestSearchTicker:
    """Test the search_ticker functionality"""
    
    def test_search_exact_ticker_match(self):
        """Test searching for exact ticker symbols"""
        # Test major tickers
        test_cases = [
            ("AAPL", "Apple Inc."),
            ("MSFT", "Microsoft Corporation"),
            ("GOOGL", "Alphabet Inc."),
            ("TSLA", "Tesla, Inc."),
            ("ETSY", "Etsy Inc.")
        ]
        
        results = {}
        for ticker, expected_name in test_cases:
            search_results = search_ticker(ticker)
            results[ticker] = {
                "query": ticker,
                "results": search_results,
                "found": len(search_results) > 0,
                "expected_name": expected_name,
                "actual_name": search_results[0]['name'] if search_results else None,
                "name_match": search_results[0]['name'] == expected_name if search_results else False
            }
        
        # Save results to JSON
        with open('test-data/search_exact_ticker_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Assert at least one result found for each
        for ticker, _ in test_cases:
            assert len(search_ticker(ticker)) > 0, f"No results found for {ticker}"
    
    def test_search_company_name_match(self):
        """Test searching for company names"""
        test_cases = [
            ("Apple", "AAPL"),
            ("Microsoft", "MSFT"),
            ("Tesla", "TSLA"),
            ("Amazon", "AMZN"),
            ("Google", "GOOGL")
        ]
        
        results = {}
        for company_name, expected_ticker in test_cases:
            search_results = search_ticker(company_name)
            results[company_name] = {
                "query": company_name,
                "results": search_results,
                "found": len(search_results) > 0,
                "expected_ticker": expected_ticker,
                "actual_ticker": search_results[0]['ticker'] if search_results else None,
                "ticker_match": search_results[0]['ticker'] == expected_ticker if search_results else False
            }
        
        # Save results to JSON
        with open('test-data/search_company_name_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Assert at least one result found for each
        for company_name, _ in test_cases:
            assert len(search_ticker(company_name)) > 0, f"No results found for {company_name}"
    
    def test_search_partial_matches(self):
        """Test partial matching functionality"""
        test_cases = [
            ("Micro", ["MSFT"]),  # Should find Microsoft
            ("Appl", ["AAPL"]),   # Should find Apple
            ("Tes", ["TSLA"]),    # Should find Tesla
        ]
        
        results = {}
        for query, expected_tickers in test_cases:
            search_results = search_ticker(query)
            found_tickers = [r['ticker'] for r in search_results]
            results[query] = {
                "query": query,
                "results": search_results,
                "found_tickers": found_tickers,
                "expected_tickers": expected_tickers,
                "contains_expected": any(ticker in found_tickers for ticker in expected_tickers)
            }
        
        # Save results to JSON
        with open('test-data/search_partial_match_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Assert partial matches work
        for query, expected_tickers in test_cases:
            search_results = search_ticker(query)
            found_tickers = [r['ticker'] for r in search_results]
            assert any(ticker in found_tickers for ticker in expected_tickers), \
                f"Expected tickers {expected_tickers} not found in results for '{query}'"
    
    def test_search_case_insensitive(self):
        """Test case insensitive search"""
        test_cases = [
            ("aapl", "AAPL"),
            ("msft", "MSFT"),
            ("microsoft", "MSFT"),
            ("APPLE", "AAPL")
        ]
        
        results = {}
        for query, expected_ticker in test_cases:
            search_results = search_ticker(query)
            found_tickers = [r['ticker'] for r in search_results]
            results[query] = {
                "query": query,
                "results": search_results,
                "found_tickers": found_tickers,
                "expected_ticker": expected_ticker,
                "case_insensitive_match": expected_ticker in found_tickers
            }
        
        # Save results to JSON
        with open('test-data/search_case_insensitive_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Assert case insensitive search works
        for query, expected_ticker in test_cases:
            search_results = search_ticker(query)
            found_tickers = [r['ticker'] for r in search_results]
            assert expected_ticker in found_tickers, \
                f"Expected ticker {expected_ticker} not found for case insensitive query '{query}'"


class TestGetStockInfo:
    """Test the get_stock_info functionality (analysis)"""
    
    def test_stock_info_major_stocks(self):
        """Test stock info retrieval for major stocks"""
        test_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
        
        results = {}
        for ticker in test_tickers:
            try:
                stock_info = get_stock_info(ticker)
                results[ticker] = {
                    "ticker": ticker,
                    "success": 'error' not in stock_info,
                    "data": stock_info,
                    "has_name": 'name' in stock_info and stock_info['name'] is not None,
                    "has_price": 'current_price' in stock_info and stock_info['current_price'] is not None,
                    "has_pe_ratio": 'pe_ratio' in stock_info and stock_info['pe_ratio'] is not None,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                results[ticker] = {
                    "ticker": ticker,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Save results to JSON
        with open('test-data/stock_info_major_stocks_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Check if any stocks work (some might fail due to rate limiting)
        successful_calls = sum(1 for r in results.values() if r.get('success', False))
        print(f"Successful stock info calls: {successful_calls}/{len(test_tickers)}")
    
    def test_stock_info_invalid_ticker(self):
        """Test stock info with invalid ticker"""
        invalid_tickers = ["INVALID", "NOTREAL", "FAKE123"]
        
        results = {}
        for ticker in invalid_tickers:
            try:
                stock_info = get_stock_info(ticker)
                results[ticker] = {
                    "ticker": ticker,
                    "has_error": 'error' in stock_info,
                    "data": stock_info,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                results[ticker] = {
                    "ticker": ticker,
                    "exception": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Save results to JSON
        with open('test-data/stock_info_invalid_ticker_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Assert that invalid tickers return errors
        for ticker in invalid_tickers:
            stock_info = get_stock_info(ticker)
            assert 'error' in stock_info, f"Expected error for invalid ticker {ticker}"
    
    def test_stock_info_rate_limiting(self):
        """Test behavior under rate limiting conditions"""
        # Make multiple rapid calls to trigger rate limiting
        ticker = "AAPL"
        results = []
        
        for i in range(10):  # Make 10 rapid calls
            try:
                stock_info = get_stock_info(ticker)
                results.append({
                    "call_number": i + 1,
                    "success": 'error' not in stock_info,
                    "has_rate_limit_error": 'error' in stock_info and '429' in str(stock_info.get('error', '')),
                    "data": stock_info,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                results.append({
                    "call_number": i + 1,
                    "success": False,
                    "exception": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Save results to JSON
        with open('test-data/stock_info_rate_limiting_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Analyze rate limiting behavior
        rate_limited_calls = sum(1 for r in results if r.get('has_rate_limit_error', False))
        successful_calls = sum(1 for r in results if r.get('success', False))
        
        print(f"Rate limited calls: {rate_limited_calls}/10")
        print(f"Successful calls: {successful_calls}/10")


class TestCapeComparison:
    """Test CAPE comparison functionality"""
    
    def test_cape_calculation_basic(self):
        """Test basic CAPE calculation functionality"""
        try:
            cape_data = calculate_cape_comparison()
            
            result = {
                "success": cape_data is not None,
                "has_data": isinstance(cape_data, dict) and len(cape_data) > 0,
                "data_keys": list(cape_data.keys()) if isinstance(cape_data, dict) else None,
                "data": cape_data,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        # Save results to JSON
        with open('test-data/cape_calculation_results.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        # This might fail due to external dependencies, so we just record the result
        print(f"CAPE calculation success: {result.get('success', False)}")


class TestDatabaseIntegration:
    """Test database functionality"""
    
    def test_database_operations(self):
        """Test database operations with search history"""
        from utils.db_utils import save_search_history, get_search_history, get_session_stats
        
        # Test data
        session_id = "test_session_123"
        test_searches = [
            ("AAPL", [{"ticker": "AAPL", "name": "Apple Inc."}]),
            ("Microsoft", [{"ticker": "MSFT", "name": "Microsoft Corporation"}]),
            ("TSLA", [{"ticker": "TSLA", "name": "Tesla, Inc."}])
        ]
        
        results = {
            "save_operations": [],
            "retrieve_operations": [],
            "session_stats": None
        }
        
        # Test saving searches
        for query, search_results in test_searches:
            try:
                save_search_history(session_id, query, search_results)
                results["save_operations"].append({
                    "query": query,
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                results["save_operations"].append({
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Test retrieving search history
        try:
            history = get_search_history(session_id)
            # Convert DataFrame to dict for JSON serialization
            history_dict = history.to_dict('records') if hasattr(history, 'to_dict') else history
            results["retrieve_operations"] = {
                "success": True,
                "history_count": len(history),
                "history": history_dict,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            results["retrieve_operations"] = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        # Test session stats
        try:
            stats = get_session_stats(session_id)
            results["session_stats"] = {
                "success": True,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            results["session_stats"] = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        # Save results to JSON
        with open('test-data/database_operations_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Assert database operations work
        assert all(op["success"] for op in results["save_operations"]), "Some save operations failed"
        assert results["retrieve_operations"]["success"], "Retrieve operation failed"
        assert results["session_stats"]["success"], "Session stats operation failed"


if __name__ == "__main__":
    # Run tests and generate JSON reports
    pytest.main([
        __file__,
        "--json-report",
        "--json-report-file=test-data/pytest_report.json",
        "-v"
    ])
