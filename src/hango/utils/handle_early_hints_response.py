class HandleEarlyHintsResponse:
    def __extract_header_info(self, header):
        print("[header]", header)
        if 'sec-fetch-dest' in header and 'sec-fetch-mode' in header and 'accept' in header:
            dest, mode, accept = header['sec-fetch-dest'], header['sec-fetch-mode'], header['accept']
            return (dest, mode, accept) 
        return (None, None, None)
        
    def __get_hints(self, header, path):
        dest, mode, accept = self.__extract_header_info(header)
        hints = {}
        if dest != None and mode != None and accept != None:
            if dest == 'document' and mode == 'navigate' and "text/html" in accept:
                hints = {"url": path, "rel": "preload", "as": "style", "type": "text/css"}
            elif dest in ("fetch", "empty") and "application/json" in accept:
                hints = {"url": path, "rel": "preload", "as": "fetch", "type": "application/json"}
            elif dest == "image":
                hints = {"url": path, "rel": "preload", "as": "image", "type": "application/octet-stream"}
            return hints
        else:
            return hints

        
    def handle_early_hints_response(self, header, path):
        hints = self.__get_hints(header, path)
        print("hints returned: ", hints)
        return hints
