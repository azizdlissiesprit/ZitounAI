package tn.zitouna.ai.assistant;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/** parcelId is optional: with it, irrigation/yield questions are answered for that parcel. */
public record ChatRequest(@NotBlank @Size(max = 1000) String message, Long parcelId) {
}
