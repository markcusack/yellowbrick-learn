package com.example.rag_demo;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
class AIController {
    private final ChatService chatService;

    AIController(ChatService chatService) {
        this.chatService = chatService;
    }
    @GetMapping("/chat")
    public Map chat(@RequestParam(name = "query") String query) {
        return Map.of("answer", chatService.chat(query));
    }
}