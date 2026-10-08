package tn.zitouna.ai.assistant.modules;

import org.springframework.stereotype.Service;

/** maladie -> M1. STUB: M1 needs a leaf photo, which the chat cannot send yet. */
@Service
public class DiseaseChatStub implements DiseaseService {

    @Override
    public ModuleAnswer answer(ChatContext ctx) {
        // TODO(M1): when the chat accepts images, call DiseaseClient.predict(image) and answer with
        //  the disease (labelFr) and the treatment advice.
        return ModuleAnswer.stub("Bech na3ref el mardh, ab3athli taswira wadh7a mta3 war9a mel page « Diagnostic ».");
    }
}
