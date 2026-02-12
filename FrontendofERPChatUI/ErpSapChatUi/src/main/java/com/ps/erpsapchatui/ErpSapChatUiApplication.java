package com.ps.erpsapchatui;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class ErpSapChatUiApplication {

    public static void main(String[] args) {
        SpringApplication.run(ErpSapChatUiApplication.class, args);
    }

}
