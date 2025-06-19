class SimulationState:
    # 모드/플래그
    auto_mode = True
    awaiting_inbound_input = None
    request_add_bot = False
    request_remove_bot = False
    # 큐
    manual_requests: list[tuple[str, int]] = []
    auto_requests:   list[str] = []
