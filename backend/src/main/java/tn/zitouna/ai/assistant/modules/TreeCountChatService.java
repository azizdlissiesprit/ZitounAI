package tn.zitouna.ai.assistant.modules;

import java.time.ZoneId;
import java.util.List;

import org.springframework.stereotype.Service;

import tn.zitouna.ai.assistant.ChatLink;
import tn.zitouna.parcel.Parcel;

/**
 * comptage -> M6. Counting needs a top view of the parcel, which the chat cannot receive: the reply
 * sends the farmer to the tree counting page (button), and recalls the count saved on the parcel.
 */
@Service
public class TreeCountChatService implements TreeCountService {

    static final String ASK_IMAGE = "ابعثلي تصويرة من الفوق (درون ولا ساتليت) متاع أرضك، ونوريك قداش فيها من زيتونة.";
    static final String LINK_LABEL = "افتح صفحة عدّ الزيتون";

    @Override
    public ModuleAnswer answer(ChatContext ctx) {
        Parcel parcel = ctx.parcel();
        ChatLink link = new ChatLink(LINK_LABEL, parcel == null ? "/tree-count" : "/tree-count?parcel=" + parcel.getId());
        if (parcel == null || parcel.getTreeCount() == null) {
            return new ModuleAnswer(ASK_IMAGE, null, false, List.of(), link);
        }
        String when = parcel.getTreeCountedAt() == null ? ""
                : " (آخر عدّ: %s)".formatted(parcel.getTreeCountedAt().atZone(ZoneId.of("Africa/Tunis")).toLocalDate());
        String reply = "في القطعة « %s » مسجلين %d زيتونة%s. باش تعاود تحسبهم، %s"
                .formatted(parcel.getName(), parcel.getTreeCount(), when, ASK_IMAGE);
        Fact fact = Fact.of("parcelle", false,
                "nombre_arbres_enregistre", parcel.getTreeCount(),
                "date_comptage", parcel.getTreeCountedAt() == null ? null
                        : parcel.getTreeCountedAt().atZone(ZoneId.of("Africa/Tunis")).toLocalDate(),
                "source_comptage", parcel.getTreeCountSource(),
                "densite_arbres_par_ha", parcel.getDensityPerHa(),
                "densite_estimee", parcel.getDensityEstimated(),
                "comment_recompter", "bouton « " + LINK_LABEL + " » sous la réponse : envoyer une image vue du dessus");
        return new ModuleAnswer(reply, null, false, List.of(fact), link);
    }
}
