import nltk
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
from nltk.util import ngrams
from operator import itemgetter

class Parse():
    def __init__(self):
        self.extra_stop_words = [
            "show"
        ]
        self.stopwords = stopwords.words('english')
        self.stopwords.extend(self.extra_stop_words)
        self.skip_words = [
            "all",
            "any",
            "anything",
            "display",
            "every",
            "everything",
            "find",
            "show",
            "some",
            "something",
            "want"
        ]
        self.stemmer = PorterStemmer()
        self.tokenizer = nltk.PunktWordTokenizer()

    def preparation(self, q):
        # used_query = q.lower().strip()
        used_query = q
        result = {
            "used_query": used_query,
            "original_query": q
        }
        raw_tokens = self.tokenizer.tokenize(used_query)
        token_spans = self.tokenizer.span_tokenize(used_query)
        tagged_words = nltk.pos_tag(raw_tokens)

        result["tokens"] = []
        for index, value in enumerate(raw_tokens):
            lower_value = value.lower()
            stop_word = lower_value in self.stopwords
            skip_word = lower_value in self.skip_words
            result["tokens"].append({
                "value": lower_value,
                "start": token_spans[index][0],
                "end": token_spans[index][1],
                "pos": tagged_words[index][1],
                "use": tagged_words[index][1][0] in ["J", "N", "V"] and not stop_word and not skip_word,
                "stem": self.stemmer.stem(lower_value),
                "stop_word": stop_word,
                "skip_word": skip_word
            })

        return result

    def create_found_doc(self, term, tokens, found_item, start, end):
        return {
            "term": term,
            "tokens": tokens,
            "found_item": found_item,
            "start": start,
            "end": end
        }

    def find_matches(self, ngram_size, tokens, vocab, existing=None, can_not_match=None):
        if existing is None:
            existing = []
        if can_not_match is None:
            can_not_match = []
        res = {
            "found": [],
            "can_not_match": can_not_match
        }

        n = min(len(tokens), ngram_size)
        for ngram in ngrams(tokens, n):
            ngram_term = " ".join(
                x["value"] for x in ngram if not x["stop_word"]
            )
            start = ngram[0]["start"]
            end = ngram[-1:][0]["end"]

            if ngram_term in vocab["en"]:
                if not any([x for x in existing if x["start"] == start and x["end"] == end]):
                    res["found"].append(
                        self.create_found_doc(
                            ngram_term,
                            [x["value"] for x in ngram],
                            vocab["en"][ngram_term],
                            start,
                            end
                        )
                    )
            elif n > 0:
                res["found"].extend(
                    self.find_matches(
                        n-1,
                        tokens,
                        vocab,
                        existing=res["found"],
                        can_not_match=res["can_not_match"]
                    )["found"]
                )
            elif n == 0 and ngram[0]["use"] and ngram[0]["pos"][0] in ["J", "N", "V"]:
                res["can_not_match"].append(ngram[0])

        return res

    def autocorrect_query(self, used_query, found_entities):
        corrected_query = used_query
        corrected = False
        # need to work from end of string backwards otherwise it gets messed up with adding/removing chars
        for entity in sorted(found_entities, key=itemgetter("start"), reverse=True):
            for x in [x for x in entity["found_item"] if x["match_type"] == "spelling"]:
                corrected = True
                corrected_query = corrected_query[0:entity["start"]] + x["display_name"] + corrected_query[entity["end"]:]

        if corrected:
            return corrected_query
        else:
            return None

    def unique_matches(self, found_entities):
        flattened = [{
            "type": x["type"],
            "key": x["key"],
            "source": x["source"]
        } for entity in found_entities for x in entity["found_item"]]

        return list({v['type']+v['key']:v for v in flattened}.values())

    def unique_non_detections(self, can_not_match):
        return list(set(x["value"] for x in can_not_match))

    def disambiguate(self, vocab, preparation_result):
        found_entities = self.find_matches(
            3,
            preparation_result["tokens"],
            vocab
        )

        autocorrected_query = self.autocorrect_query(
            preparation_result["used_query"],
            found_entities["found"]
        )

        unique_entities = self.unique_matches(found_entities["found"])
        res = {
            "detections": unique_entities,
            "non_detections": self.unique_non_detections(found_entities["can_not_match"])
        }
        if autocorrected_query is not None:
            res["autocorrected_query"] = autocorrected_query

        return res

