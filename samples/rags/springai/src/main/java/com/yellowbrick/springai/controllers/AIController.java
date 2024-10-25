package com.yellowbrick.springai.controllers;

import com.yellowbrick.springai.service.ChatService;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
class AIController {
    private final ChatClient chatClient;
    private final ChatService chatBotService;

    AIController(ChatClient chatClient, ChatService chatBotService) {
        this.chatBotService = chatBotService;
        this.chatClient = chatClient;
    }
    @GetMapping("/ai")
    Map<String, String> completion(@RequestParam(value = "message", defaultValue = "Tell me a joke") String message) {
        return Map.of(
                "completion",
                chatClient.prompt()
                        .user(message)
                        .call()
                        .content());
    }

    @GetMapping("/chat")
    public Map chat(@RequestParam(name = "query") String query) {
        return Map.of("answer", chatBotService.chat(query));
    }
}