"""Test news website APIs."""
import os
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

BASE_URL = "http://localhost:8001/api"

def test_categories():
    """Test category creation and retrieval."""
    print("\n=== Testing Categories ===")

    # Create categories
    categories = [
        {"name": "Technology", "description": "Tech news and updates"},
        {"name": "Business", "description": "Business and finance news"},
        {"name": "Science", "description": "Scientific discoveries"},
        {"name": "Entertainment", "description": "Movies, music, and culture"}
    ]

    created_categories = []
    for cat in categories:
        response = requests.post(f"{BASE_URL}/categories", json=cat)
        if response.status_code == 200:
            print(f"✓ Created category: {cat['name']}")
            created_categories.append(response.json())
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"✓ Category already exists: {cat['name']}")
        else:
            print(f"✗ Failed to create category {cat['name']}: {response.status_code} - {response.text}")

    # Get all categories
    response = requests.get(f"{BASE_URL}/categories")
    if response.status_code == 200:
        categories = response.json()
        print(f"✓ Retrieved {len(categories)} categories")
        assert len(categories) >= 4, f"Expected at least 4 categories, got {len(categories)}"
    else:
        print(f"✗ Failed to get categories: {response.status_code}")
        assert False, "Failed to get categories"

    return categories


def test_articles(categories):
    """Test article creation, retrieval, and update."""
    print("\n=== Testing Articles ===")

    # Create an article
    article_data = {
        "title": "The Future of AI in Technology",
        "content": "Artificial Intelligence is rapidly transforming the technology landscape. From machine learning algorithms to neural networks, AI is enabling computers to perform tasks that were once thought to be exclusively human. The integration of AI in various sectors, including healthcare, finance, and transportation, is revolutionizing how we live and work. Companies are investing billions in AI research and development, and the pace of innovation shows no signs of slowing down. As we look to the future, it's clear that AI will play an increasingly central role in shaping our world.",
        "category": "Technology",
        "author": "Test Author"
    }

    response = requests.post(f"{BASE_URL}/articles", json=article_data)
    if response.status_code == 200:
        article = response.json()
        print(f"✓ Created article: {article['title']}")
        print(f"  AI Summary: {article['summary'][:100]}...")

        # Verify summary was generated
        assert article['summary'], "Summary should be generated"
        assert len(article['summary']) > 0, "Summary should not be empty"
        assert article['id'], "Article should have an ID"
        article_id = article['id']
    else:
        print(f"✗ Failed to create article: {response.status_code} - {response.text}")
        assert False, "Failed to create article"

    # Get all articles
    response = requests.get(f"{BASE_URL}/articles")
    if response.status_code == 200:
        articles = response.json()
        print(f"✓ Retrieved {len(articles)} articles")
        assert len(articles) >= 1, "Should have at least 1 article"
    else:
        print(f"✗ Failed to get articles: {response.status_code}")
        assert False, "Failed to get articles"

    # Get single article (this increments view count)
    response = requests.get(f"{BASE_URL}/articles/{article_id}")
    if response.status_code == 200:
        article = response.json()
        print(f"✓ Retrieved article by ID: {article['title']}")
        print(f"  Views: {article['views']}")
        assert article['views'] >= 1, "Views should be incremented"
    else:
        print(f"✗ Failed to get article by ID: {response.status_code}")
        assert False, "Failed to get article by ID"

    # Update article
    update_data = {
        "title": "The Future of AI in Technology (Updated)"
    }
    response = requests.put(f"{BASE_URL}/articles/{article_id}", json=update_data)
    if response.status_code == 200:
        updated_article = response.json()
        print(f"✓ Updated article title: {updated_article['title']}")
        assert "Updated" in updated_article['title'], "Title should be updated"
    else:
        print(f"✗ Failed to update article: {response.status_code}")
        assert False, "Failed to update article"

    # Track share
    response = requests.post(f"{BASE_URL}/articles/{article_id}/share")
    if response.status_code == 200:
        print(f"✓ Tracked article share")
    else:
        print(f"✗ Failed to track share: {response.status_code}")
        assert False, "Failed to track share"

    # Verify share count increased
    response = requests.get(f"{BASE_URL}/articles/{article_id}")
    if response.status_code == 200:
        article = response.json()
        print(f"  Shares: {article['shares']}")
        assert article['shares'] >= 1, "Shares should be incremented"

    # Filter by category
    response = requests.get(f"{BASE_URL}/articles?category=Technology")
    if response.status_code == 200:
        tech_articles = response.json()
        print(f"✓ Retrieved {len(tech_articles)} Technology articles")
        assert len(tech_articles) >= 1, "Should have at least 1 Technology article"
    else:
        print(f"✗ Failed to filter by category: {response.status_code}")
        assert False, "Failed to filter by category"

    return article_id


def test_delete_article(article_id):
    """Test article deletion."""
    print("\n=== Testing Article Deletion ===")

    response = requests.delete(f"{BASE_URL}/articles/{article_id}")
    if response.status_code == 200:
        print(f"✓ Deleted article {article_id}")
    else:
        print(f"✗ Failed to delete article: {response.status_code}")
        assert False, "Failed to delete article"

    # Verify article is deleted
    response = requests.get(f"{BASE_URL}/articles/{article_id}")
    if response.status_code == 404:
        print(f"✓ Confirmed article is deleted")
    else:
        print(f"✗ Article still exists after deletion")
        assert False, "Article should not exist after deletion"


if __name__ == "__main__":
    print("Starting News Website API Tests")
    print("=" * 50)

    try:
        # Test categories
        categories = test_categories()

        # Test articles
        article_id = test_articles(categories)

        # Test deletion
        test_delete_article(article_id)

        print("\n" + "=" * 50)
        print("✓ All tests passed!")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        exit(1)
