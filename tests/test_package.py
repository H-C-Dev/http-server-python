def test_import_and_version():
    import hango
    assert hasattr(hango, "__version__")
