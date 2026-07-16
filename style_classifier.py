from collections import Counter


class StyleClassifier:

    def classify(self, page):

        styles = {}
        next_id = 1

        for block in page.blocks:

            key = self.make_style_key(block)

            if key not in styles:
                styles[key] = next_id
                next_id += 1

            block.style_id = styles[key]

        return styles

    def make_style_key(self, block):

        spans = []

        for line in block.lines:
            spans.extend(line.spans)

        if not spans:
            return ("", 0, 0, 0)

        # Longest span
        span = max(spans, key=lambda s: len(s.text))

        return (
            span.font,
            round(span.size),
            span.flags,
        )