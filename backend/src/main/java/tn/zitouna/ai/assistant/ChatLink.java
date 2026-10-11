package tn.zitouna.ai.assistant;

/**
 * Button under a chat reply that opens a page of the app.
 *
 * @param label text of the button (derja, Arabic script)
 * @param url   app route, e.g. "/tree-count?parcel=3"
 */
public record ChatLink(String label, String url) {
}
