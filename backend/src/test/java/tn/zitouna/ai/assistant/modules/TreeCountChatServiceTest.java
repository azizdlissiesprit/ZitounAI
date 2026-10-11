package tn.zitouna.ai.assistant.modules;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Instant;

import org.junit.jupiter.api.Test;

import tn.zitouna.parcel.Parcel;
import tn.zitouna.parcel.TreeCountSource;

/** comptage: Arabic reply + button to the tree counting page. */
class TreeCountChatServiceTest {

    private final TreeCountChatService service = new TreeCountChatService();

    @Test
    void withoutParcelAsksForATopViewAndLinksToTheCountingPage() {
        ModuleAnswer answer = service.answer(new ChatContext(1L, "9adech 3andi mn zitouna?", null, null));
        assertThat(answer.reply()).isEqualTo(TreeCountChatService.ASK_IMAGE);
        assertThat(answer.link().url()).isEqualTo("/tree-count");
        assertThat(answer.link().label()).isEqualTo("افتح صفحة عدّ الزيتون");
        assertThat(answer.mock()).isFalse();
    }

    @Test
    void withACountedParcelRecallsTheSavedCount() {
        Parcel parcel = new Parcel();
        parcel.setId(7L);
        parcel.setName("Henchir Sfax");
        parcel.setTreeCount(142);
        parcel.setTreeCountedAt(Instant.parse("2026-10-11T10:00:00Z"));
        parcel.setTreeCountSource(TreeCountSource.CORRECTED);

        ModuleAnswer answer = service.answer(new ChatContext(1L, "9adech 3andi?", parcel, null));

        assertThat(answer.reply()).contains("Henchir Sfax", "142", "2026-10-11", TreeCountChatService.ASK_IMAGE);
        assertThat(answer.link().url()).isEqualTo("/tree-count?parcel=7");
        assertThat(answer.facts().getFirst().data()).containsEntry("nombre_arbres_enregistre", 142)
                .containsEntry("source_comptage", TreeCountSource.CORRECTED);
    }
}
