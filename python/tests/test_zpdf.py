import pytest
import zpdf
from pathlib import Path

# Test files
TEST_DIR = Path(__file__).parent.parent.parent
TEST_PDF = TEST_DIR / "test" / "test.pdf"
TAGGED_PDF = TEST_DIR / "benchmark" / "PDFUA-Ref-2-08_BookChapter.pdf"
ACROBAT_PDF = TEST_DIR / "test" / "acrobat_reference.pdf"


class TestDocumentOpen:
    """Test document opening from various sources."""

    def test_open_file_path_str(self):
        with zpdf.Document(str(TEST_PDF)) as doc:
            assert doc.page_count > 0

    def test_open_file_path_object(self):
        with zpdf.Document(TEST_PDF) as doc:
            assert doc.page_count > 0

    def test_open_bytes(self):
        with open(TEST_PDF, "rb") as f:
            data = f.read()
        with zpdf.Document(data) as doc:
            assert doc.page_count > 0

    def test_open_nonexistent_file(self):
        with pytest.raises(zpdf.InvalidPdfError):
            zpdf.Document("/nonexistent/path.pdf")

    def test_open_invalid_pdf(self, tmp_path):
        invalid = tmp_path / "invalid.pdf"
        invalid.write_text("not a pdf")
        # Invalid PDFs may or may not raise - zpdf is permissive
        # Just verify it doesn't crash
        try:
            with zpdf.Document(str(invalid)) as doc:
                pass  # May succeed with empty pages
        except zpdf.InvalidPdfError:
            pass  # Expected for clearly invalid files


class TestDocumentProperties:
    """Test document properties and metadata."""

    def test_page_count(self):
        with zpdf.Document(TEST_PDF) as doc:
            assert isinstance(doc.page_count, int)
            assert doc.page_count >= 1

    def test_page_info(self):
        with zpdf.Document(TEST_PDF) as doc:
            info = doc.get_page_info(0)
            assert info.width > 0
            assert info.height > 0
            assert isinstance(info.rotation, int)

    def test_page_info_invalid(self):
        with zpdf.Document(TEST_PDF) as doc:
            with pytest.raises(zpdf.PageNotFoundError):
                doc.get_page_info(9999)


class TestTextExtraction:
    """Test text extraction functionality."""

    def test_extract_page(self):
        with zpdf.Document(TEST_PDF) as doc:
            text = doc.extract_page(0)
            assert isinstance(text, str)
            assert len(text) > 0

    def test_extract_all(self):
        with zpdf.Document(TEST_PDF) as doc:
            text = doc.extract_all()
            assert isinstance(text, str)
            assert len(text) > 0

    def test_extract_all_multiple_pages(self):
        if ACROBAT_PDF.exists():
            with zpdf.Document(ACROBAT_PDF) as doc:
                text = doc.extract_all()
                # Should have page separators (form feed)
                assert doc.page_count > 1
                assert isinstance(text, str)

    def test_extract_page_invalid(self):
        with zpdf.Document(TEST_PDF) as doc:
            with pytest.raises(zpdf.PageNotFoundError):
                doc.extract_page(9999)

    def test_extract_page_negative(self):
        with zpdf.Document(TEST_PDF) as doc:
            with pytest.raises(zpdf.PageNotFoundError):
                doc.extract_page(-1)

    def test_extract_empty_page(self):
        # Some PDFs may have empty pages
        with zpdf.Document(TEST_PDF) as doc:
            text = doc.extract_page(0)
            # Just verify it returns a string (may be empty)
            assert isinstance(text, str)


class TestTaggedPDF:
    """Test extraction from tagged PDFs (PDF/UA)."""

    @pytest.mark.skipif(not TAGGED_PDF.exists(), reason="Tagged PDF not available")
    def test_extract_tagged_pdf(self):
        with zpdf.Document(TAGGED_PDF) as doc:
            text = doc.extract_all()
            assert isinstance(text, str)
            assert len(text) > 0

    @pytest.mark.skipif(not TAGGED_PDF.exists(), reason="Tagged PDF not available")
    def test_extract_tagged_page(self):
        with zpdf.Document(TAGGED_PDF) as doc:
            for i in range(min(5, doc.page_count)):
                text = doc.extract_page(i)
                assert isinstance(text, str)


class TestIteration:
    """Test document iteration."""

    def test_iteration(self):
        with zpdf.Document(TEST_PDF) as doc:
            pages = list(doc)
            assert len(pages) == doc.page_count
            for text in pages:
                assert isinstance(text, str)

    def test_iteration_empty_after_exhaust(self):
        with zpdf.Document(TEST_PDF) as doc:
            pages1 = list(doc)
            pages2 = list(doc)  # Should start from beginning
            assert len(pages1) == len(pages2)


class TestContextManager:
    """Test context manager behavior."""

    def test_context_manager_closes(self):
        with zpdf.Document(TEST_PDF) as doc:
            _ = doc.page_count
        with pytest.raises(ValueError, match="closed"):
            _ = doc.page_count

    def test_explicit_close(self):
        doc = zpdf.Document(TEST_PDF)
        assert doc.page_count > 0
        doc.close()
        with pytest.raises(ValueError, match="closed"):
            _ = doc.page_count

    def test_double_close_safe(self):
        doc = zpdf.Document(TEST_PDF)
        doc.close()
        doc.close()  # Should not raise


class TestBounds:
    """Test text extraction with bounding boxes."""

    def test_extract_bounds(self):
        with zpdf.Document(TEST_PDF) as doc:
            spans = doc.extract_bounds(0)
            assert isinstance(spans, list)
            if spans:  # May be empty for some PDFs
                span = spans[0]
                assert hasattr(span, 'text')
                assert hasattr(span, 'x0')
                assert hasattr(span, 'y0')
                assert hasattr(span, 'x1')
                assert hasattr(span, 'y1')

    def test_extract_bounds_invalid_page(self):
        with zpdf.Document(TEST_PDF) as doc:
            with pytest.raises(zpdf.PageNotFoundError):
                doc.extract_bounds(9999)


class TestErrorHandling:
    """Test error handling."""

    def test_error_types(self):
        # Verify error types exist
        assert issubclass(zpdf.InvalidPdfError, Exception)
        assert issubclass(zpdf.ExtractionError, Exception)
        assert issubclass(zpdf.PageNotFoundError, Exception)


class TestMemory:
    """Test memory handling."""

    def test_large_document(self):
        if ACROBAT_PDF.exists():
            with zpdf.Document(ACROBAT_PDF) as doc:
                # Extract all pages to test memory handling
                text = doc.extract_all()
                assert len(text) > 0

    def test_repeated_extraction(self):
        with zpdf.Document(TEST_PDF) as doc:
            # Extract same page multiple times
            for _ in range(10):
                text = doc.extract_page(0)
                assert isinstance(text, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
