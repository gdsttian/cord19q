"""
Report module
"""

import os
import os.path
import sys

from .models import Models
from .query import Query

class Report(object):
    """
    Methods to build reports from a series of queries
    """

    @staticmethod
    def write(output, line):
        """
        Writes line to output file.

        Args:
            output: output file
            line: line to write
        """

        output.write("%s<br/>\n" % line)

    @staticmethod
    def build(embeddings, db, queries, outfile):
        """
        Builds a report using a list of input queries

        Args:
            embeddings: embeddings model
            db: open SQLite database
            queries: list of queries to execute
            outfile: report output file
        """

        with open(outfile, "w") as output:
            cur = db.cursor()

            for query in queries:
                output.write("# %s\n" % query)

                # Query for best matches
                results = Query.search(embeddings, cur, query, 50)

                # Extract top sections as highlights
                Report.write(output, "#### Highlights")
                for highlight in Query.highlights(results, 5):
                    Report.write(output, "- %s" % Query.text(highlight))

                # Write each article result
                Report.write(output, "\n#### Articles")

                # Get results grouped by document
                documents = Query.documents(results)

                # Print each result, sorted by max score descending
                for uid in sorted(documents, key=lambda k: sum([x[0] for x in documents[k]]), reverse=True)[:10]:
                    cur.execute("SELECT Title, Reference, Authors, Publication, Published from articles where id = ?", [uid])
                    article = cur.fetchone()

                    Report.write(output, "[%s](%s)" % (article[0], article[1]))

                    if article[2]:
                        Report.write(output, "by %s" % article[2])

                    # Publication name and date
                    publication = article[3] if article[3] else None
                    if article[4]:
                        published = Query.date(article[4])
                        publication = (publication + " - " + published) if publication else published

                    if publication and len(publication) > 0:
                        Report.write(output, "*%s*" % publication)

                    # Print top matches
                    for _, text in documents[uid]:
                        Report.write(output, "- %s" % Query.text(text))

                    # Start new section
                    output.write("\n")

    @staticmethod
    def run(task, path):
        """
        Reads a list of queries from a task file and builds a report.

        Args:
            task: input task file
            path: model path
        """

        # Load model
        embeddings, db = Models.load(path)

        # Read each task query
        with open(task, "r") as f:
            queries = f.readlines()

        # Build the report file
        Report.build(embeddings, db, queries, "%s.md" % os.path.splitext(task)[0])

        # Free resources
        Models.close(db)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        Report.run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
