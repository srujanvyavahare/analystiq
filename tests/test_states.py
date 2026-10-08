from unittest.mock import patch
import ui.components.states as states

def test_render_empty_state():
    with patch("streamlit.markdown") as mock_markdown:
        states.render_empty_state("x", "y", "z")
        mock_markdown.assert_called_once()
    mock_markdown.assert_called_once()
