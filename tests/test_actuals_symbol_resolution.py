"""Unit tests for company symbol resolution fallbacks (D-099)."""

from unittest.mock import patch, MagicMock
from opi.actuals import resolve_company_symbols_and_urls


def test_symbol_resolution_fallbacks():
    """D-099: Symbol resolution resolves symbols from Next.js JSON or issue page fallbacks."""
    # 1. Next.js JSON embedding (e.g. Bombay Coated: "nse_symbol":"BCSSL")
    mock_json_html = '''
    <html>
      <head><title>IPO Details</title></head>
      <body>
        <script>
          self.__next_f.push([1, "{\\"nse_symbol\\":\\"BCSSL\\",\\"bse_scripcode\\":\\"544999\\"}"]);
        </script>
      </body>
    </html>
    '''
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = mock_json_html

    with patch("requests.get", return_value=mock_resp):
        res = resolve_company_symbols_and_urls(
            "Bombay Coated & Special Steels",
            features={"overview_url": "https://www.chittorgarh.com/ipo/bombay-coated-and-special-steels-ipo/2671/"}
        )
        assert res["nse_symbol"] == "BCSSL"
        assert res["bse_code"] == "544999"

    # 2. il_nse_script_symbol fallback
    mock_il_html = '''
    <html>
      <body>
        <script>
          {"il_nse_script_symbol":"TESTSYM","il_bse_script_code":"544123"}
        </script>
      </body>
    </html>
    '''
    mock_resp_il = MagicMock()
    mock_resp_il.status_code = 200
    mock_resp_il.text = mock_il_html

    with patch("requests.get", return_value=mock_resp_il):
        res_il = resolve_company_symbols_and_urls(
            "Test Company",
            features={"overview_url": "https://www.chittorgarh.com/ipo/test-company-ipo/1234/"}
        )
        assert res_il["nse_symbol"] == "TESTSYM"
        assert res_il["bse_code"] == "544123"

    # 3. Graceful fallback when no symbols are present
    mock_empty_html = "<html><body>No symbol info yet</body></html>"
    mock_resp_empty = MagicMock()
    mock_resp_empty.status_code = 200
    mock_resp_empty.text = mock_empty_html

    with patch("requests.get", return_value=mock_resp_empty):
        res_empty = resolve_company_symbols_and_urls(
            "Unlisted IPO",
            features={"overview_url": "https://www.chittorgarh.com/ipo/unlisted-ipo/9999/"}
        )
        assert res_empty["nse_symbol"] is None
        assert res_empty["bse_code"] is None
