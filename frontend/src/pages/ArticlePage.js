import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Share2, Twitter, Facebook, Linkedin, MessageCircle, Copy } from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const API = `${API_BASE}/api`;
const MY_HOMEPAGE_URL = API_BASE?.match(/-([a-z0-9]+)\./)?.[1]
  ? `https://${API_BASE?.match(/-([a-z0-9]+)\./)?.[1]}.previewer.live`
  : window.location.origin;

export default function ArticlePage() {
  const { id } = useParams();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copySuccess, setCopySuccess] = useState(false);

  useEffect(() => {
    fetchArticle();
  }, [id]);

  const fetchArticle = async () => {
    try {
      const response = await axios.get(`${API}/articles/${id}`);
      setArticle(response.data);
    } catch (error) {
      console.error("Error fetching article:", error);
    } finally {
      setLoading(false);
    }
  };

  const trackShare = async () => {
    try {
      await axios.post(`${API}/articles/${id}/share`);
    } catch (error) {
      console.error("Error tracking share:", error);
    }
  };

  const handleShare = (platform) => {
    trackShare();
    const url = `${MY_HOMEPAGE_URL}/article/${id}`;
    const title = article.title;

    const shareUrls = {
      twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`,
      whatsapp: `https://wa.me/?text=${encodeURIComponent(title + ' ' + url)}`
    };

    if (shareUrls[platform]) {
      window.open(shareUrls[platform], '_blank', 'width=600,height=400');
    }
  };

  const handleCopyLink = () => {
    const url = `${MY_HOMEPAGE_URL}/article/${id}`;
    navigator.clipboard.writeText(url);
    setCopySuccess(true);
    trackShare();
    setTimeout(() => setCopySuccess(false), 2000);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Loading article...</p>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Article not found</p>
          <Link to="/">
            <Button>Back to Home</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-700">
            <span className="mr-2">←</span>
            <span className="font-semibold">NewsHub</span>
          </Link>
        </div>
      </header>

      {/* Article Content */}
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <article>
          {/* Article Header */}
          <div className="bg-white rounded-lg shadow-sm p-8 mb-6">
            <div className="mb-4">
              <Badge variant="secondary" className="mb-2">{article.category}</Badge>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">{article.title}</h1>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span>By {article.author}</span>
                <span>•</span>
                <span>{formatDate(article.created_at)}</span>
                <span>•</span>
                <span>👁️ {article.views} views</span>
              </div>
            </div>
          </div>

          {/* AI Summary */}
          <Card className="mb-6 border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <span>✨</span> AI-Generated Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700">{article.summary}</p>
            </CardContent>
          </Card>

          {/* Article Content */}
          <div className="bg-white rounded-lg shadow-sm p-8 mb-6">
            <div className="prose max-w-none">
              <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {article.content}
              </div>
            </div>
          </div>

          {/* Share Section */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Share2 className="w-5 h-5" />
                Share this article
              </CardTitle>
              <CardDescription>
                📤 {article.shares} shares so far
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={() => handleShare('twitter')}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Twitter className="w-4 h-4" />
                  Twitter
                </Button>
                <Button
                  onClick={() => handleShare('facebook')}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Facebook className="w-4 h-4" />
                  Facebook
                </Button>
                <Button
                  onClick={() => handleShare('linkedin')}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Linkedin className="w-4 h-4" />
                  LinkedIn
                </Button>
                <Button
                  onClick={() => handleShare('whatsapp')}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <MessageCircle className="w-4 h-4" />
                  WhatsApp
                </Button>
                <Button
                  onClick={handleCopyLink}
                  variant={copySuccess ? "default" : "outline"}
                  className="flex items-center gap-2"
                >
                  <Copy className="w-4 h-4" />
                  {copySuccess ? "Copied!" : "Copy Link"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </article>
      </main>
    </div>
  );
}
