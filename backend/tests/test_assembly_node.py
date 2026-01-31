
def test_assembly_node_missing_files():
    """
    Unit test for assembly_node ensuring it fails when files are missing.
    """
    from orchestration import assembly_node
    
    # Mock state with a non-existent file
    state = {
        "retrieved_clips": [
            {"video_path": "c:/non_existent_file_123.mp4", "segment_order": 1},
            {"video_path": "c:/non_existent_file_456.mp4", "segment_order": 2}
        ]
    }
    
    result = assembly_node(state)
    
    assert result.get("current_phase") == "assembly_failed"
    assert "Missing video files" in result.get("error")
