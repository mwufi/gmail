import lxml
from lxml.html.clean import Cleaner


def clean_html(html):
    try:
        cleaner = Cleaner()
        cleaner.javascript = (
            True  # This is True because we want to activate the javascript filter
        )
        cleaner.style = True  # This is True because we want to activate the styles & stylesheet filter
        before = html
        after = cleaner.clean_html(html)
        # TODO: log this!!
        # print(f"BEFORE: {len(before)}")
        # print(f"AFTER: {len(after)}")
        return after
    except Exception as e:
        print(f"Error cleaning HTML: ------------------------------ {e}", html)
        return html


if __name__ == "__main__":
    cleaner = Cleaner()
    cleaner.javascript = (
        True  # This is True because we want to activate the javascript filter
    )
    cleaner.style = (
        True  # This is True because we want to activate the styles & stylesheet filter
    )

    print("WITH JAVASCRIPT & STYLES")
    print(lxml.html.tostring(lxml.html.parse("http://www.google.com")))
    print("WITHOUT JAVASCRIPT & STYLES")
    print(
        lxml.html.tostring(cleaner.clean_html(lxml.html.parse("http://www.google.com")))
    )
