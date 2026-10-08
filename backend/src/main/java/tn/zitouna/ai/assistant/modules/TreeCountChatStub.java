package tn.zitouna.ai.assistant.modules;

import org.springframework.stereotype.Service;

/** comptage -> M6. STUB: M6 needs a drone / satellite image, which the chat cannot send yet. */
@Service
public class TreeCountChatStub implements TreeCountService {

    @Override
    public ModuleAnswer answer(ChatContext ctx) {
        // TODO(M6): when the chat accepts images, call TreeCountClient.count(image) and answer with treeCount.
        if (ctx.parcel() != null && ctx.parcel().getTreeCount() != null) {
            return ModuleAnswer.stub("Fil parcelle « %s » msajlin %d zitouna. Bech n3awed na7sebhom, ab3athli taswira mel drone walla satellite fil page mta3 el parcelle."
                    .formatted(ctx.parcel().getName(), ctx.parcel().getTreeCount()));
        }
        return ModuleAnswer.stub(
                "Ab3athli taswira mel drone walla satellite fil page mta3 el parcelle, w ena n7asbelek 3add el zitoun.");
    }
}
