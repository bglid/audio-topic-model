import hashlib
from pathlib import Path

import spacy
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer


# Defining a function to create topic graphs
def create_topic_graph(driver, docs, topics, topic_model):
    """To create a neo4j Knowledge Graph based on the extracted data from the topic model. We accomplish this by the following:
    1. Creating Topic Nodes.
    2. Creating Document Nodes and relationships between each doc and their corresponding topic.
    3. Creating Keyword Nodes and Strength relationships to their associated topic.

    Args:
        driver : Variable representing the connected GraphDatabase
        docs (_type_): Docs used for topic modeling
        topics (_type_): topics extracted from BERTopic
        topic_model (_type_): Topic Model fit during topic modeling
    """
    # Initializing driver session to write to KG:
    with driver.session() as session:
        # Creating the topic nodes:
        topic_ids = set(topics)
        topic_queries = [
            {
                "key": generate_topic_key(topic_model.get_topic(topic_id)),
                "keywords": ", ".join(
                    [word for word, proba in topic_model.get_topic(topic_id)]
                ),
            }
            for topic_id in topic_ids
        ]

        # Merge/creating topic nodes with keywords
        session.run(
            """
            UNWIND $topics AS topic
            MERGE (t:Topic {key: topic.key})
            SET t.keywords = topic.keywords
            """,
            topics=topic_queries,
        )

        # querying doc relationships
        doc_queries = [
            {
                "content": doc,
                "topic_key": generate_topic_key(topic_model.get_topic(topic)),
            }
            for doc, topic in zip(docs, topics)
        ]

        # Creating document nodes and relationships between the doc and topic
        session.run(
            """
            UNWIND $docs AS doc
            MERGE (d:Document {content: doc.content})
            WITH d, doc
            MATCH (t:Topic {key: doc.topic_key})
            MERGE (d)-[:BELONGS_TO]->(t)
            """,
            docs=doc_queries,
        )

        # Adding keyword and strength relationships to the topic
        for topic_id in topic_ids:
            topic_key = generate_topic_key(topic_model.get_topic(topic_id))
            keywords = topic_model.get_topic(topic_id)
            for keyword, strength in keywords:
                session.run(
                    """
                    MERGE (k:Keyword {word: $keyword})
                    WITH k
                    MATCH (t:Topic {key: $topic_key})
                    MERGE (k)-[r:REPRESENTS]->(t)
                    SET r.strength = $strength
                    """,
                    keyword=keyword,
                    topic_key=topic_key,
                    strength=strength,
                )


# defining a function that allows us to have unique keys for each topic
def generate_topic_key(keywords):
    keywords_string = "_".join([kw for kw, _ in keywords])
    return hashlib.md5(keywords_string.encode(), usedforsecurity=False).hexdigest()


def topic_modeling(input, output, name, uri, auth_username, auth_password):
    """_summary_

    Args:
        input string: input directory containing data that topic modeling should be run on.
        output string: Output directory/location. Defaults to within this directory but can be changed.
        name string: Name of run, used for output directory.
        uri string: URI to Neo4j DB
        auth_username string: Username for Neo4j DB
        auth_password string: Password for Neo4j DB
    """

    # processing a test document and creating a spacy object
    user_audio = Path(input)
    # NOTE need to process audio

    # converting pdf into docs to process
    docs = []
    # iterating through and grabbing raw text to iterate through
    # needed for topic modeler
    for line in user_audio:
        if line.text_with_ws.isalnum():
            docs.append(line.text_with_ws)

    # Creating a list of basic french stopwords to remove using CountVectorizer:
    fr_stopwords = []
    # with open("../Radicalism_Verbalized_NLP/sample_data/fr_stopwords.txt", "r") as f:
    with open("./sample_data/fr_stopwords.txt") as f:
        text = f.read()
        for i in text.split("\n"):
            fr_stopwords.append(i)

    # Creating a custom vectorizer model & representation model to help remove stopwords
    vectorizer_model = CountVectorizer(stop_words=fr_stopwords)
    representation_model = KeyBERTInspired()
    # Setting up our French-supported embedding model from HF embeddings:
    embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # Initializing our BERTopic model for the HF embeddings
    topic_model = BERTopic(
        embedding_model=embedding_model,
        vectorizer_model=vectorizer_model,
        representation_model=representation_model,
    )
    # topics, probs = topic_model.fit_transform(docs)
    topics, probs = topic_model.fit_transform(docs)
    # quick debug...;.;.
    print(topics)

    # Writing the topic results to a local directory
    with open(f"{output}{name}.csv", "w") as write_file:
        # writing topic results to csv
        topic_info = topic_model.get_document_info(docs)
        topic_info.to_csv(write_file, index=False)

    # URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
    URI = uri  # database uri link
    AUTH = (auth_username, auth_password)  # username + password

    # Verifying connection
    driver = GraphDatabase.driver(URI, auth=AUTH)
    driver.verify_connectivity()

    create_topic_graph(
        driver=driver, docs=docs, topics=topics, topic_model=topic_model
    )  # Actually writes to our Neo4j Knowledge Graph Database
