"""k-nearest few-shot example selection using TF-IDF cosine similarity."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from openswitch.models import Example


class KNearestFewShot:
    """Selects top-k nearest training examples to construct few-shot prompts."""

    def __init__(self, train_examples: list[Example], k: int = 3):
        self.k = max(1, min(k, len(train_examples))) if train_examples else 0
        self.examples = train_examples
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)

        if self.examples:
            corpus = [ex.input for ex in self.examples]
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        else:
            self.tfidf_matrix = None

    def get_nearest_examples(self, query_text: str, k: int | None = None) -> list[Example]:
        """Find the top-k most similar training examples by cosine similarity."""
        if not self.examples or self.tfidf_matrix is None:
            return []

        num_k = k or self.k
        num_k = min(num_k, len(self.examples))

        query_vec = self.vectorizer.transform([query_text])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Get top-k indices descending
        top_indices = similarities.argsort()[::-1][:num_k]
        return [self.examples[idx] for idx in top_indices]

    def format_kshot_messages(
        self,
        query_text: str,
        system_prompt: str | None = None,
        k: int | None = None,
    ) -> list[dict[str, str]]:
        """Construct full chat messages list including few-shot demonstrations."""
        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        nearest = self.get_nearest_examples(query_text, k=k)
        for ex in nearest:
            messages.append({"role": "user", "content": ex.input})
            messages.append({"role": "assistant", "content": ex.reference})

        # Add target query
        messages.append({"role": "user", "content": query_text})
        return messages
