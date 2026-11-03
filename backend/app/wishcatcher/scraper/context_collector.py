"""
Context Collector - Colectează context complet (post + comentarii) din multiple surse
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import praw
import time
import re
import os


@dataclass
class RedditContext:
    """Context complet Reddit"""
    post_id: str
    post_title: str
    post_text: str
    post_author: Optional[str]
    post_timestamp: float
    post_upvotes: int
    subreddit: str
    comments: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dict"""
        return {
            "post_id": self.post_id,
            "post_title": self.post_title,
            "post_text": self.post_text,
            "post_author": self.post_author,
            "post_timestamp": self.post_timestamp,
            "post_upvotes": self.post_upvotes,
            "subreddit": self.subreddit,
            "comments": self.comments,
            "metadata": self.metadata
        }


class ContextCollector:
    """Colectează context complet din multiple surse"""
    
    def __init__(self):
        self.reddit_client = None  # Initialize with PRAW if needed
        self.rate_limiter = RateLimiter(max_requests=60, time_window=60)
    
    async def collect_from_source(
        self,
        source: str,
        filters: Optional[Dict] = None,
        limit: int = 100
    ) -> List[RedditContext]:
        """
        Colectează context din sursă specificată
        
        Args:
            source: Sursa (reddit, quora, gumtree, etc.)
            filters: Filtre geografice/culturale
            limit: Număr maxim de context-uri
        """
        if source == "reddit":
            return await self._collect_reddit(filters, limit)
        elif source == "quora":
            return await self._collect_quora(filters, limit)
        elif source == "gumtree":
            return await self._collect_gumtree(filters, limit)
        elif source == "mumsnet":
            return await self._collect_mumsnet(filters, limit)
        elif source == "moneysavingexpert":
            return await self._collect_moneysavingexpert(filters, limit)
        elif source == "indiehackers":
            return await self._collect_indiehackers(filters, limit)
        elif source == "hackernews":
            return await self._collect_hackernews(filters, limit)
        elif source == "producthunt":
            return await self._collect_producthunt(filters, limit)
        elif source == "youtube":
            return await self._collect_youtube(filters, limit)
        elif source == "softpedia":
            return await self._collect_softpedia(filters, limit)
        elif source == "studentroom":
            return await self._collect_studentroom(filters, limit)
        elif source == "ukbusinessforums":
            return await self._collect_ukbusinessforums(filters, limit)
        elif source == "imobiliare":
            return await self._collect_imobiliare(filters, limit)
        elif source == "trustpilot":
            return await self._collect_trustpilot(filters, limit)
        elif source == "petitiideclic":
            return await self._collect_petitiideclic(filters, limit)
        elif source == "undelucram":
            return await self._collect_undelucram(filters, limit)
        elif source == "anpc":
            return await self._collect_anpc(filters, limit)
        else:
            return []
    
    async def _collect_reddit(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe Reddit"""
        contexts = []
        
        # UK subreddits (extinse)
        uk_subreddits = [
            "unitedkingdom", "london", "AskUK", "CasualUK",
            "UKPersonalFinance", "UKFrugal", "UKJobs", "UKProperty",
            "UKHealthcare", "UKLegalAdvice", "UKEntrepreneur", "UKStartups",
            "UKTech", "UKPersonalFinance", "UKFrugal"
        ]
        
        # RO subreddits (extinse)
        ro_subreddits = [
            "Romania", "bucuresti", "programare", "RoFrugal",
            "rorep", "RomaniaPorn", "RomaniaSocial", "RomaniaJobs",
            "RomaniaTech", "RomaniaBusiness", "RomaniaStartups",
            "cluj", "iasi", "timisoara", "constanta"
        ]
        
        # Select subreddits based on filters
        subreddits = []
        if filters:
            geo = filters.get("geography", {}).get("level", "global")
            if geo == "uk" or geo == "united_kingdom":
                subreddits = uk_subreddits
            elif geo == "romania":
                subreddits = ro_subreddits
            else:
                subreddits = uk_subreddits + ro_subreddits
        else:
            subreddits = uk_subreddits + ro_subreddits
        
        # Reddit search queries pentru România (dacă e cazul)
        search_queries = []
        if filters:
            geo = filters.get("geography", {}).get("level", "global")
            language = filters.get("language", "all")
            
            # Query-uri specifice pentru r/Romania și r/Programare
            if geo == "romania" and language == "ro":
                # Categoria 1: Lipsă și Absență
                search_queries.extend([
                    "de ce nu există în românia",
                    "de ce nu există la noi",
                    "nu se găsește la noi",
                    "unde pot găsi în RO",
                    "alternativă românească la",
                    "singura opțiune este",
                    "există vreo aplicație pentru"
                ])
                # Categoria 2: Frustrare și Eșec
                search_queries.extend([
                    "m-am săturat de",
                    "este un calvar să",
                    "bătaie de joc",
                    "nu răspunde nimeni la",
                    "groaznic",
                    "mizerabil",
                    "deja a 3-a oară când"
                ])
                # Categoria 4: Birocrație și Software
                search_queries.extend([
                    "cum se declară",
                    "eroare e-factura",
                    "eroare e-transport",
                    "cum automatizez",
                    "program de gestiune care să",
                    "export excel",
                    "integrare cu"
                ])
        
        # Collect from each subreddit
        max_subreddits = min(5, len(subreddits))
        
        # Dacă avem search queries, folosim search pentru subreddit-urile românești
        if search_queries and any(s in ["Romania", "programare"] for s in subreddits):
            for subreddit_name in ["Romania", "programare"]:
                if subreddit_name not in subreddits:
                    continue
                for query in search_queries[:10]:  # Limit to 10 queries
                    try:
                        # Reddit search endpoint
                        url = f"https://www.reddit.com/r/{subreddit_name}/search.json"
                        params = {
                            "q": query,
                            "limit": min(limit // len(search_queries), 10),
                            "sort": "new",
                            "t": "month"  # Search in last month
                        }
                        
                        await self.rate_limiter.wait_if_needed()
                        headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url, params=params, headers=headers) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    posts = data.get("data", {}).get("children", [])
                                    
                                    for post_data in posts:
                                        post = post_data.get("data", {})
                                        post_text = post.get("selftext", "") or post.get("title", "")
                                        
                                        if not post_text or len(post_text.strip()) < 20:
                                            continue
                                        
                                        if post_text.lower() in ["[deleted]", "[removed]"]:
                                            continue
                                        
                                        try:
                                            context = RedditContext(
                                                post_id=post.get("id", ""),
                                                post_title=post.get("title", "")[:500],
                                                post_text=post_text[:5000],
                                                post_author=post.get("author"),
                                                post_timestamp=post.get("created_utc", time.time()),
                                                post_upvotes=post.get("ups", 0),
                                                subreddit=subreddit_name,
                                                comments=[],
                                                metadata={
                                                    "url": f"https://reddit.com{post.get('permalink', '')}",
                                                    "search_query": query,
                                                    "source_type": "reddit_search"
                                                }
                                            )
                                            contexts.append(context)
                                        except Exception as e:
                                            print(f"[WARNING] Error creating search context: {e}")
                                            continue
                        
                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"[ERROR] Error searching r/{subreddit_name} with query '{query}': {e}")
                        continue
        
        # Collect normal posts from subreddits
        for subreddit_name in subreddits[:max_subreddits]:
            try:
                # Use Reddit JSON endpoint (no auth needed)
                url = f"https://www.reddit.com/r/{subreddit_name}/new.json"
                per_subreddit_limit = max(1, limit // max_subreddits)
                params = {
                    "limit": min(per_subreddit_limit, 25),
                    "t": "week"  # Changed to week for fresher content
                }
                
                await self.rate_limiter.wait_if_needed()
                
                headers = {
                    "User-Agent": "WishCatcher/1.0 (Educational Research)"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            posts = data.get("data", {}).get("children", [])
                            print(f"[DEBUG] Reddit {subreddit_name}: {len(posts)} posts found")
                            
                            for post_data in posts:
                                post = post_data.get("data", {})
                                
                                # Skip if no text
                                post_text = post.get("selftext", "") or post.get("title", "")
                                if not post_text or len(post_text.strip()) < 20:
                                    continue
                                
                                # Skip deleted/removed posts
                                if post_text.lower() in ["[deleted]", "[removed]"]:
                                    continue
                                
                                # Create context directly from post data (faster, no extra API call)
                                try:
                                    context = RedditContext(
                                        post_id=post.get("id", ""),
                                        post_title=post.get("title", "")[:500],
                                        post_text=post_text[:5000],  # Limit text length
                                        post_author=post.get("author"),
                                        post_timestamp=post.get("created_utc", time.time()),
                                        post_upvotes=post.get("ups", 0),
                                        subreddit=subreddit_name,
                                        comments=[],  # Comments can be added later if needed
                                        metadata={
                                            "url": f"https://reddit.com{post.get('permalink', '')}",
                                            "num_comments": post.get("num_comments", 0)
                                        }
                                    )
                                    contexts.append(context)
                                except Exception as e:
                                    print(f"[WARNING] Error creating context for post {post.get('id')}: {e}")
                                    continue
                
                await asyncio.sleep(1)  # Rate limiting
            
            except Exception as e:
                print(f"[ERROR] Error collecting from r/{subreddit_name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Contextual understanding needs same-author clarifications. The old
        # collector returned only opening posts (comments=[]), even though a
        # full post+replies reader already existed. Hydrate a bounded number
        # of unique threads before intent extraction; keep originals when
        # Reddit denies access or replies are missing.
        if os.getenv("WISHCATCHER_REDDIT_FETCH_COMMENTS", "1") == "1":
            try:
                maximum = min(max(int(os.getenv("WISHCATCHER_REDDIT_MAX_ENRICHED", "8")), 0), 30)
            except ValueError:
                maximum = 8
            contexts = await self._enrich_reddit_threads(contexts, max_threads=maximum)

        print(f"[DEBUG] Reddit collection complete: {len(contexts)} contexts collected")
        return contexts

    async def _enrich_reddit_threads(
        self, contexts: List[RedditContext], max_threads: int = 8
    ) -> List[RedditContext]:
        """Hydrate post+comments for a bounded set, retaining original metadata.

        No new query sources are introduced, no secrets are required, and
        failures are recoverable. Respect platform permissions and rate limits.
        """
        if max_threads <= 0 or not contexts:
            return contexts
        seen = set()
        enriched_count = 0
        result = []
        for original in contexts:
            ident = (original.subreddit, original.post_id)
            if ident in seen:
                # Search and new-post feeds frequently overlap; avoid re-scoring
                # the same Reddit discussion as independent market demand.
                continue
            seen.add(ident)
            if enriched_count < max_threads and original.post_id and original.subreddit:
                enriched_count += 1
                try:
                    full = await self._collect_reddit_post_context(
                        original.post_id, original.subreddit
                    )
                except Exception:
                    full = None
                if full:
                    full.metadata = {**original.metadata, **full.metadata}
                    if not full.post_text:
                        full.post_text = original.post_text
                    if not full.post_title:
                        full.post_title = original.post_title
                    result.append(full)
                    continue
            result.append(original)
        return result
    
    async def _collect_reddit_post_context(
        self,
        post_id: str,
        subreddit: str
    ) -> Optional[RedditContext]:
        """Colectează context complet pentru un post Reddit"""
        try:
            # Get post + comments from JSON endpoint
            url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
            
            await self.rate_limiter.wait_if_needed()
            
            headers = {"User-Agent": "WishCatcher/1.1 (context research; contact operator)"}
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Post data
                        post_data = data[0]["data"]["children"][0]["data"]
                        
                        # Comments data
                        comments_data = data[1]["data"]["children"]
                        
                        # Extract comments
                        comments = self._extract_reddit_comments(comments_data)
                        
                        # Calculate metadata
                        metadata = {
                            "total_comments": len(comments),
                            "total_upvotes": post_data.get("score", 0) + sum(
                                c.get("upvotes", 0) for c in comments
                            ),
                            "engagement_score": min(
                                (post_data.get("score", 0) / max(len(comments), 1)) * 0.5 +
                                (len(comments) / 100) * 0.5,
                                1.0
                            ),
                            "discussion_depth": max(
                                (c.get("depth", 0) for c in comments),
                                default=0
                            )
                        }
                        
                        return RedditContext(
                            post_id=post_data.get("id"),
                            post_title=post_data.get("title", ""),
                            post_text=post_data.get("selftext", ""),
                            post_author=post_data.get("author"),
                            post_timestamp=post_data.get("created_utc", 0),
                            post_upvotes=post_data.get("score", 0),
                            subreddit=subreddit,
                            comments=comments,
                            metadata=metadata
                        )
        
        except Exception as e:
            print(f"Error collecting context for post {post_id}: {e}")
            return None
    
    def _extract_reddit_comments(self, comments_data: List) -> List[Dict]:
        """Extrage comentarii recursive"""
        comments = []
        
        for comment_item in comments_data:
            if comment_item.get("kind") == "t1":  # Comment
                comment_data = comment_item.get("data", {})
                
                if comment_data.get("body") != "[deleted]":
                    comment = {
                        "id": comment_data.get("id"),
                        "text": comment_data.get("body", ""),
                        "author": comment_data.get("author"),
                        "timestamp": comment_data.get("created_utc", 0),
                        "upvotes": comment_data.get("score", 0),
                        "depth": comment_data.get("depth", 0)
                    }
                    
                    # Extract replies
                    if comment_data.get("replies"):
                        replies_data = comment_data["replies"].get("data", {}).get("children", [])
                        comment["replies"] = self._extract_reddit_comments(replies_data)
                    
                    comments.append(comment)
        
        return comments
    
    async def _collect_quora(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe Quora"""
        contexts = []
        
        # Quora search URLs based on filters
        search_queries = []
        if filters:
            geo = filters.get("geography", {}).get("level", "global")
            language = filters.get("language", "all")
            
            if geo == "uk" or geo == "united_kingdom":
                search_queries = [
                    "UK business ideas",
                    "UK startup ideas",
                    "UK problems",
                    "UK needs"
                ]
            elif geo == "romania":
                if language == "ro":
                    # Query-uri în română pentru căutare mai precisă
                    search_queries = [
                        "idei de business România",
                        "startup România",
                        "probleme România",
                        "ce lipsește România",
                        "servicii România",
                        "aplicații România",
                        "mi-aș dori România",
                        "ar fi util România"
                    ]
                else:
                    search_queries = [
                        "Romania business ideas",
                        "Romania startup ideas",
                        "Romania problems",
                        "Romania needs"
                    ]
            else:
                search_queries = [
                    "business ideas",
                    "startup ideas",
                    "problems need solutions",
                    "what do people need"
                ]
        else:
            search_queries = ["business ideas", "startup ideas", "problems need solutions"]
        
        for query in search_queries[:3]:  # Limit queries
            try:
                url = f"https://www.quora.com/search?q={query.replace(' ', '+')}"
                
                await self.rate_limiter.wait_if_needed()
                
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find question links
                            question_links = soup.find_all('a', href=True)
                            for link in question_links[:limit // len(search_queries)]:
                                href = link.get('href', '')
                                if '/question/' in href:
                                    question_url = f"https://www.quora.com{href}" if href.startswith('/') else href
                                    context = await self._collect_quora_question(question_url)
                                    if context:
                                        contexts.append(context)
                
                await asyncio.sleep(2)  # Rate limiting
            
            except Exception as e:
                print(f"Error collecting from Quora query '{query}': {e}")
                continue
        
        return contexts
    
    async def _collect_quora_question(self, url: str) -> Optional[RedditContext]:
        """Colectează o întrebare Quora cu răspunsuri"""
        try:
            await self.rate_limiter.wait_if_needed()
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract question
                        question_elem = soup.find('div', class_='q-text') or soup.find('h1')
                        question_text = question_elem.get_text(strip=True) if question_elem else ""
                        
                        # Extract answers
                        answer_elems = soup.find_all('div', class_='AnswerBase') or soup.find_all('div', {'data-testid': 'answer'})
                        comments = []
                        for i, answer in enumerate(answer_elems[:10]):  # Top 10 answers
                            answer_text = answer.get_text(strip=True)
                            if answer_text:
                                comments.append({
                                    "id": f"answer_{i}",
                                    "text": answer_text,
                                    "author": None,
                                    "timestamp": 0,
                                    "upvotes": 0,
                                    "depth": 0
                                })
                        
                        if question_text:
                            return RedditContext(
                                post_id=url.split('/')[-1],
                                post_title=question_text[:200],
                                post_text=question_text,
                                post_author=None,
                                post_timestamp=time.time(),
                                post_upvotes=len(comments),
                                subreddit="quora",
                                comments=comments,
                                metadata={"source": "quora", "url": url}
                            )
        
        except Exception as e:
            print(f"Error collecting Quora question {url}: {e}")
            return None
    
    async def _collect_gumtree(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe Gumtree (UK marketplace)"""
        contexts = []
        
        # Gumtree search URLs
        if filters and filters.get("geography", {}).get("level") in ["uk", "united_kingdom"]:
            search_queries = [
                "wanted",
                "looking for",
                "need"
            ]
            
            for query in search_queries:
                try:
                    url = f"https://www.gumtree.com/search?q={query.replace(' ', '+')}"
                    
                    await self.rate_limiter.wait_if_needed()
                    
                    async with aiohttp.ClientSession() as session:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Find listing links
                                listing_links = soup.find_all('a', href=True)
                                for link in listing_links[:limit // len(search_queries)]:
                                    href = link.get('href', '')
                                    if '/p/' in href or '/a/' in href:
                                        listing_url = f"https://www.gumtree.com{href}" if href.startswith('/') else href
                                        context = await self._collect_gumtree_listing(listing_url)
                                        if context:
                                            contexts.append(context)
                    
                    await asyncio.sleep(2)
                
                except Exception as e:
                    print(f"Error collecting from Gumtree query '{query}': {e}")
                    continue
        
        return contexts
    
    async def _collect_gumtree_listing(self, url: str) -> Optional[RedditContext]:
        """Colectează un listing Gumtree"""
        try:
            await self.rate_limiter.wait_if_needed()
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract title
                        title_elem = soup.find('h1') or soup.find('title')
                        title = title_elem.get_text(strip=True) if title_elem else ""
                        
                        # Extract description
                        desc_elem = soup.find('div', class_='description') or soup.find('p', class_='description')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        if title or description:
                            return RedditContext(
                                post_id=url.split('/')[-1],
                                post_title=title[:200],
                                post_text=description,
                                post_author=None,
                                post_timestamp=time.time(),
                                post_upvotes=0,
                                subreddit="gumtree",
                                comments=[],
                                metadata={"source": "gumtree", "url": url}
                            )
        
        except Exception as e:
            print(f"Error collecting Gumtree listing {url}: {e}")
            return None
    
    async def _collect_mumsnet(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe Mumsnet (UK parenting forum)"""
        contexts = []
        
        if filters and filters.get("geography", {}).get("level") in ["uk", "united_kingdom"]:
            try:
                # Mumsnet discussion boards
                boards = [
                    "https://www.mumsnet.com/talk",
                    "https://www.mumsnet.com/talk/am_i_being_unreasonable",
                    "https://www.mumsnet.com/talk/am_i_being_unreasonable?page=2"
                ]
                
                for board_url in boards:
                    await self.rate_limiter.wait_if_needed()
                    
                    async with aiohttp.ClientSession() as session:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        async with session.get(board_url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Find discussion links
                                discussion_links = soup.find_all('a', href=True)
                                for link in discussion_links[:limit // len(boards)]:
                                    href = link.get('href', '')
                                    if '/talk/' in href and '/am_i_being_unreasonable' not in href:
                                        discussion_url = f"https://www.mumsnet.com{href}" if href.startswith('/') else href
                                        context = await self._collect_mumsnet_discussion(discussion_url)
                                        if context:
                                            contexts.append(context)
                    
                    await asyncio.sleep(2)
            
            except Exception as e:
                print(f"Error collecting from Mumsnet: {e}")
        
        return contexts
    
    async def _collect_mumsnet_discussion(self, url: str) -> Optional[RedditContext]:
        """Colectează o discuție Mumsnet"""
        try:
            await self.rate_limiter.wait_if_needed()
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract title
                        title_elem = soup.find('h1') or soup.find('title')
                        title = title_elem.get_text(strip=True) if title_elem else ""
                        
                        # Extract posts
                        post_elems = soup.find_all('div', class_='post') or soup.find_all('article')
                        comments = []
                        main_text = ""
                        
                        for i, post in enumerate(post_elems[:20]):  # Top 20 posts
                            post_text = post.get_text(strip=True)
                            if i == 0:
                                main_text = post_text
                            else:
                                comments.append({
                                    "id": f"post_{i}",
                                    "text": post_text,
                                    "author": None,
                                    "timestamp": 0,
                                    "upvotes": 0,
                                    "depth": 0
                                })
                        
                        if title or main_text:
                            return RedditContext(
                                post_id=url.split('/')[-1],
                                post_title=title[:200],
                                post_text=main_text,
                                post_author=None,
                                post_timestamp=time.time(),
                                post_upvotes=len(comments),
                                subreddit="mumsnet",
                                comments=comments,
                                metadata={"source": "mumsnet", "url": url}
                            )
        
        except Exception as e:
            print(f"Error collecting Mumsnet discussion {url}: {e}")
            return None
    
    async def _collect_moneysavingexpert(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe MoneySavingExpert forums"""
        contexts = []
        
        if filters and filters.get("geography", {}).get("level") in ["uk", "united_kingdom"]:
            try:
                # MSE forum categories
                categories = [
                    "https://forums.moneysavingexpert.com/categories/deals-discussion",
                    "https://forums.moneysavingexpert.com/categories/debt-free-wannabe",
                    "https://forums.moneysavingexpert.com/categories/deals-discussion?page=2"
                ]
                
                for category_url in categories:
                    await self.rate_limiter.wait_if_needed()
                    
                    async with aiohttp.ClientSession() as session:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        async with session.get(category_url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Find topic links
                                topic_links = soup.find_all('a', href=True)
                                for link in topic_links[:limit // len(categories)]:
                                    href = link.get('href', '')
                                    if '/discussion/' in href:
                                        topic_url = f"https://forums.moneysavingexpert.com{href}" if href.startswith('/') else href
                                        context = await self._collect_mse_topic(topic_url)
                                        if context:
                                            contexts.append(context)
                    
                    await asyncio.sleep(2)
            
            except Exception as e:
                print(f"Error collecting from MoneySavingExpert: {e}")
        
        return contexts
    
    async def _collect_mse_topic(self, url: str) -> Optional[RedditContext]:
        """Colectează un topic MoneySavingExpert"""
        try:
            await self.rate_limiter.wait_if_needed()
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract title
                        title_elem = soup.find('h1') or soup.find('title')
                        title = title_elem.get_text(strip=True) if title_elem else ""
                        
                        # Extract posts
                        post_elems = soup.find_all('div', class_='post') or soup.find_all('article')
                        comments = []
                        main_text = ""
                        
                        for i, post in enumerate(post_elems[:20]):
                            post_text = post.get_text(strip=True)
                            if i == 0:
                                main_text = post_text
                            else:
                                comments.append({
                                    "id": f"post_{i}",
                                    "text": post_text,
                                    "author": None,
                                    "timestamp": 0,
                                    "upvotes": 0,
                                    "depth": 0
                                })
                        
                        if title or main_text:
                            return RedditContext(
                                post_id=url.split('/')[-1],
                                post_title=title[:200],
                                post_text=main_text,
                                post_author=None,
                                post_timestamp=time.time(),
                                post_upvotes=len(comments),
                                subreddit="moneysavingexpert",
                                comments=comments,
                                metadata={"source": "moneysavingexpert", "url": url}
                            )
        
        except Exception as e:
            print(f"Error collecting MSE topic {url}: {e}")
            return None
    
    async def _collect_indiehackers(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe Indie Hackers"""
        contexts = []
        
        try:
            # Indie Hackers discussions
            urls = [
                "https://www.indiehackers.com/posts",
                "https://www.indiehackers.com/posts?page=2"
            ]
            
            for url in urls:
                await self.rate_limiter.wait_if_needed()
                
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find post links
                            post_links = soup.find_all('a', href=True)
                            for link in post_links[:limit // len(urls)]:
                                href = link.get('href', '')
                                if '/post/' in href:
                                    post_url = f"https://www.indiehackers.com{href}" if href.startswith('/') else href
                                    context = await self._collect_indiehackers_post(post_url)
                                    if context:
                                        contexts.append(context)
                
                await asyncio.sleep(2)
        
        except Exception as e:
            print(f"Error collecting from Indie Hackers: {e}")
        
        return contexts
    
    async def _collect_indiehackers_post(self, url: str) -> Optional[RedditContext]:
        """Colectează un post Indie Hackers"""
        try:
            await self.rate_limiter.wait_if_needed()
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract title
                        title_elem = soup.find('h1') or soup.find('title')
                        title = title_elem.get_text(strip=True) if title_elem else ""
                        
                        # Extract content
                        content_elem = soup.find('div', class_='post-content') or soup.find('article')
                        content = content_elem.get_text(strip=True) if content_elem else ""
                        
                        # Extract comments
                        comment_elems = soup.find_all('div', class_='comment') or soup.find_all('article', class_='comment')
                        comments = []
                        for i, comment in enumerate(comment_elems[:10]):
                            comment_text = comment.get_text(strip=True)
                            if comment_text:
                                comments.append({
                                    "id": f"comment_{i}",
                                    "text": comment_text,
                                    "author": None,
                                    "timestamp": 0,
                                    "upvotes": 0,
                                    "depth": 0
                                })
                        
                        if title or content:
                            return RedditContext(
                                post_id=url.split('/')[-1],
                                post_title=title[:200],
                                post_text=content,
                                post_author=None,
                                post_timestamp=time.time(),
                                post_upvotes=len(comments),
                                subreddit="indiehackers",
                                comments=comments,
                                metadata={"source": "indiehackers", "url": url}
                            )
        
        except Exception as e:
            print(f"Error collecting Indie Hackers post {url}: {e}")
            return None
    
    async def _collect_hackernews(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe Hacker News"""
        contexts = []
        
        try:
            # Hacker News API (simpler than scraping)
            api_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            
            await self.rate_limiter.wait_if_needed()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        story_ids = await response.json()
                        
                        for story_id in story_ids[:limit]:
                            context = await self._collect_hn_story(story_id)
                            if context:
                                contexts.append(context)
                            await asyncio.sleep(0.5)  # Rate limiting
        
        except Exception as e:
            print(f"Error collecting from Hacker News: {e}")
        
        return contexts
    
    async def _collect_hn_story(self, story_id: int) -> Optional[RedditContext]:
        """Colectează o story Hacker News"""
        try:
            api_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            
            await self.rate_limiter.wait_if_needed()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and data.get('type') == 'story':
                            # Get comments
                            comments = []
                            if data.get('kids'):
                                for kid_id in data.get('kids', [])[:10]:
                                    comment_data = await self._get_hn_comment(kid_id)
                                    if comment_data:
                                        comments.append(comment_data)
                            
                            return RedditContext(
                                post_id=str(story_id),
                                post_title=data.get('title', '')[:200],
                                post_text=data.get('text', '') or data.get('title', ''),
                                post_author=data.get('by'),
                                post_timestamp=data.get('time', time.time()),
                                post_upvotes=data.get('score', 0),
                                subreddit="hackernews",
                                comments=comments,
                                metadata={"source": "hackernews", "url": data.get('url', '')}
                            )
        
        except Exception as e:
            print(f"Error collecting HN story {story_id}: {e}")
            return None
    
    async def _get_hn_comment(self, comment_id: int) -> Optional[Dict]:
        """Obține un comentariu Hacker News"""
        try:
            api_url = f"https://hacker-news.firebaseio.com/v0/item/{comment_id}.json"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and data.get('type') == 'comment' and data.get('text'):
                            return {
                                "id": str(comment_id),
                                "text": BeautifulSoup(data.get('text', ''), 'html.parser').get_text(),
                                "author": data.get('by'),
                                "timestamp": data.get('time', 0),
                                "upvotes": data.get('score', 0),
                                "depth": 0
                            }
        except:
            pass
        return None
    
    async def _collect_producthunt(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe Product Hunt"""
        contexts = []
        
        try:
            # Product Hunt posts
            url = "https://www.producthunt.com/posts"
            
            await self.rate_limiter.wait_if_needed()
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find product links
                        product_links = soup.find_all('a', href=True)
                        for link in product_links[:limit]:
                            href = link.get('href', '')
                            if '/products/' in href:
                                product_url = f"https://www.producthunt.com{href}" if href.startswith('/') else href
                                context = await self._collect_ph_product(product_url)
                                if context:
                                    contexts.append(context)
                                await asyncio.sleep(1)
        
        except Exception as e:
            print(f"Error collecting from Product Hunt: {e}")
        
        return contexts
    
    async def _collect_ph_product(self, url: str) -> Optional[RedditContext]:
        """Colectează un produs Product Hunt"""
        try:
            await self.rate_limiter.wait_if_needed()
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract title
                        title_elem = soup.find('h1') or soup.find('title')
                        title = title_elem.get_text(strip=True) if title_elem else ""
                        
                        # Extract description
                        desc_elem = soup.find('div', class_='description') or soup.find('p', class_='description')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        # Extract comments
                        comment_elems = soup.find_all('div', class_='comment') or soup.find_all('article')
                        comments = []
                        for i, comment in enumerate(comment_elems[:10]):
                            comment_text = comment.get_text(strip=True)
                            if comment_text:
                                comments.append({
                                    "id": f"comment_{i}",
                                    "text": comment_text,
                                    "author": None,
                                    "timestamp": 0,
                                    "upvotes": 0,
                                    "depth": 0
                                })
                        
                        if title or description:
                            return RedditContext(
                                post_id=url.split('/')[-1],
                                post_title=title[:200],
                                post_text=description,
                                post_author=None,
                                post_timestamp=time.time(),
                                post_upvotes=len(comments),
                                subreddit="producthunt",
                                comments=comments,
                                metadata={"source": "producthunt", "url": url}
                            )
        
        except Exception as e:
            print(f"Error collecting Product Hunt product {url}: {e}")
            return None
    
    async def _collect_youtube(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe YouTube (comments from videos)"""
        contexts = []
        
        # YouTube search queries
        search_queries = [
            "startup ideas",
            "business problems",
            "what do people need"
        ]
        
        # Note: YouTube API requires API key, so we'll use basic scraping
        # For production, use YouTube Data API v3
        
        try:
            for query in search_queries:
                search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                
                await self.rate_limiter.wait_if_needed()
                
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    async with session.get(search_url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            # YouTube uses dynamic content, basic scraping is limited
                            # For production, use YouTube Data API
                            
                            # Extract video IDs from HTML (simplified)
                            import re
                            video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', html)
                            
                            for video_id in video_ids[:limit // len(search_queries)]:
                                context = await self._collect_youtube_video(video_id)
                                if context:
                                    contexts.append(context)
                                await asyncio.sleep(1)
        
        except Exception as e:
            print(f"Error collecting from YouTube: {e}")
        
        return contexts
    
    async def _collect_youtube_video(self, video_id: str) -> Optional[RedditContext]:
        """Colectează un video YouTube cu comentarii"""
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            await self.rate_limiter.wait_if_needed()
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                async with session.get(video_url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract title
                        title_elem = soup.find('title')
                        title = title_elem.get_text(strip=True) if title_elem else ""
                        
                        # Extract description
                        desc_elem = soup.find('meta', {'name': 'description'})
                        description = desc_elem.get('content', '') if desc_elem else ""
                        
                        # Note: YouTube comments are loaded dynamically via JavaScript
                        # For production, use YouTube Data API v3 to get comments
                        
                        return RedditContext(
                            post_id=video_id,
                            post_title=title[:200],
                            post_text=description,
                            post_author=None,
                            post_timestamp=time.time(),
                            post_upvotes=0,
                            subreddit="youtube",
                            comments=[],  # Comments need YouTube API
                            metadata={"source": "youtube", "url": video_url, "note": "Comments require YouTube Data API"}
                        )
        
        except Exception as e:
            print(f"Error collecting YouTube video {video_id}: {e}")
            return None
    
    async def _collect_softpedia(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe Softpedia Forum (România)"""
        contexts = []
        
        # Softpedia forum URLs (inclusiv Casa Mea)
        forum_urls = [
            "https://forum.softpedia.com/forum/software/",
            "https://forum.softpedia.com/forum/gaming/",
            "https://forum.softpedia.com/forum/windows/",
            "https://forum.softpedia.com/forum/casa-mea/",  # Casa Mea - NOU
            "https://forum.softpedia.com/forum/casa-mea/instalatii/",  # Instalații
            "https://forum.softpedia.com/forum/casa-mea/izolatii/",  # Izolații
            "https://forum.softpedia.com/forum/casa-mea/fotovoltaice/"  # Fotovoltaice
        ]
        
        headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
        
        for url in forum_urls[:3]:
            try:
                await self.rate_limiter.wait_if_needed()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            threads = soup.find_all('a', href=re.compile(r'/topic/'))
                            
                            for thread in threads[:min(limit // len(forum_urls), 10)]:
                                thread_url = thread.get('href', '')
                                if thread_url:
                                    full_url = f"https://forum.softpedia.com{thread_url}" if thread_url.startswith('/') else thread_url
                                    context = await self._collect_softpedia_thread(full_url)
                                    if context:
                                        contexts.append(context)
                                        
                                if len(contexts) >= limit:
                                    break
                
                time.sleep(1)
            
            except Exception as e:
                print(f"Error collecting from Softpedia {url}: {e}")
                continue
        
        print(f"[DEBUG] Softpedia collection complete: {len(contexts)} contexts collected")
        return contexts
    
    async def _collect_softpedia_thread(self, url: str) -> Optional[RedditContext]:
        """Colectează un thread Softpedia"""
        try:
            headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        title_elem = soup.find('h1') or soup.find('title')
                        title = title_elem.get_text(strip=True) if title_elem else "No title"
                        
                        content_elem = soup.find('div', class_=re.compile(r'post|content|message'))
                        content = content_elem.get_text(strip=True) if content_elem else ""
                        
                        if len(content) < 50:
                            return None
                        
                        comments = []
                        reply_elems = soup.find_all('div', class_=re.compile(r'reply|comment|post'))
                        for reply in reply_elems[:10]:
                            reply_text = reply.get_text(strip=True)
                            if reply_text and len(reply_text) > 20:
                                comments.append({"text": reply_text})
                        
                        return RedditContext(
                            post_id=url.split('/')[-1] or "unknown",
                            post_title=title,
                            post_text=content,
                            post_author=None,
                            post_timestamp=time.time(),
                            post_upvotes=0,
                            subreddit="softpedia",
                            comments=comments,
                            metadata={"source": "softpedia", "url": url}
                        )
        
        except Exception as e:
            print(f"Error collecting Softpedia thread {url}: {e}")
            return None
    
    async def _collect_studentroom(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe The Student Room (UK)"""
        contexts = []
        
        forum_urls = [
            "https://www.thestudentroom.co.uk/forumdisplay.php?f=38",
            "https://www.thestudentroom.co.uk/forumdisplay.php?f=72"
        ]
        
        headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
        
        for url in forum_urls[:2]:
            try:
                await self.rate_limiter.wait_if_needed()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            threads = soup.find_all('a', href=re.compile(r'showthread\.php'))
                            
                            for thread in threads[:min(limit // len(forum_urls), 10)]:
                                thread_url = thread.get('href', '')
                                if thread_url:
                                    full_url = f"https://www.thestudentroom.co.uk/{thread_url}" if not thread_url.startswith('http') else thread_url
                                    context = await self._collect_studentroom_thread(full_url)
                                    if context:
                                        contexts.append(context)
                                        
                                if len(contexts) >= limit:
                                    break
                
                time.sleep(1)
            
            except Exception as e:
                print(f"Error collecting from The Student Room {url}: {e}")
                continue
        
        print(f"[DEBUG] The Student Room collection complete: {len(contexts)} contexts collected")
        return contexts
    
    async def _collect_studentroom_thread(self, url: str) -> Optional[RedditContext]:
        """Colectează un thread The Student Room"""
        try:
            headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        title_elem = soup.find('h1') or soup.find('title')
                        title = title_elem.get_text(strip=True) if title_elem else "No title"
                        
                        content_elem = soup.find('div', class_=re.compile(r'post|content|message'))
                        if not content_elem:
                            content_elem = soup.find('div', id=re.compile(r'post'))
                        content = content_elem.get_text(strip=True) if content_elem else ""
                        
                        if len(content) < 50:
                            return None
                        
                        comments = []
                        reply_elems = soup.find_all('div', class_=re.compile(r'reply|comment|post'))
                        for reply in reply_elems[:10]:
                            reply_text = reply.get_text(strip=True)
                            if reply_text and len(reply_text) > 20:
                                comments.append({"text": reply_text})
                        
                        return RedditContext(
                            post_id=url.split('=')[-1] if '=' in url else "unknown",
                            post_title=title,
                            post_text=content,
                            post_author=None,
                            post_timestamp=time.time(),
                            post_upvotes=0,
                            subreddit="studentroom",
                            comments=comments,
                            metadata={"source": "studentroom", "url": url}
                        )
        
        except Exception as e:
            print(f"Error collecting The Student Room thread {url}: {e}")
            return None
    
    async def _collect_ukbusinessforums(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe UK Business Forums"""
        contexts = []
        
        forum_urls = [
            "https://www.ukbusinessforums.co.uk/forums/starting-a-business.2/",
            "https://www.ukbusinessforums.co.uk/forums/running-a-business.3/",
            "https://www.ukbusinessforums.co.uk/forums/technology-it.15/"
        ]
        
        headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
        
        for url in forum_urls[:3]:
            try:
                await self.rate_limiter.wait_if_needed()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            threads = soup.find_all('a', href=re.compile(r'/threads/'))
                            
                            for thread in threads[:min(limit // len(forum_urls), 10)]:
                                thread_url = thread.get('href', '')
                                if thread_url:
                                    full_url = f"https://www.ukbusinessforums.co.uk{thread_url}" if thread_url.startswith('/') else thread_url
                                    context = await self._collect_ukbusinessforums_thread(full_url)
                                    if context:
                                        contexts.append(context)
                                        
                                if len(contexts) >= limit:
                                    break
                
                time.sleep(1)
            
            except Exception as e:
                print(f"Error collecting from UK Business Forums {url}: {e}")
                continue
        
        print(f"[DEBUG] UK Business Forums collection complete: {len(contexts)} contexts collected")
        return contexts
    
    async def _collect_ukbusinessforums_thread(self, url: str) -> Optional[RedditContext]:
        """Colectează un thread UK Business Forums"""
        try:
            headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        title_elem = soup.find('h1') or soup.find('title')
                        title = title_elem.get_text(strip=True) if title_elem else "No title"
                        
                        content_elem = soup.find('div', class_=re.compile(r'post|content|message'))
                        if not content_elem:
                            content_elem = soup.find('article')
                        content = content_elem.get_text(strip=True) if content_elem else ""
                        
                        if len(content) < 50:
                            return None
                        
                        comments = []
                        reply_elems = soup.find_all('div', class_=re.compile(r'reply|comment|post'))
                        for reply in reply_elems[:10]:
                            reply_text = reply.get_text(strip=True)
                            if reply_text and len(reply_text) > 20:
                                comments.append({"text": reply_text})
                        
                        return RedditContext(
                            post_id=url.split('/')[-1] or "unknown",
                            post_title=title,
                            post_text=content,
                            post_author=None,
                            post_timestamp=time.time(),
                            post_upvotes=0,
                            subreddit="ukbusinessforums",
                            comments=comments,
                            metadata={"source": "ukbusinessforums", "url": url}
                        )
        
        except Exception as e:
            print(f"Error collecting UK Business Forums thread {url}: {e}")
            return None
    
    async def _collect_imobiliare(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe Forumul Imobiliare.ro (România)"""
        contexts = []
        
        forum_urls = [
            "https://forum.imobiliare.ro/",
            "https://forum.imobiliare.ro/cumparare-vanzare/",
            "https://forum.imobiliare.ro/chirii/"
        ]
        
        headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
        
        for url in forum_urls[:3]:
            try:
                await self.rate_limiter.wait_if_needed()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            threads = soup.find_all('a', href=re.compile(r'/discutii/|/topic/'))
                            
                            for thread in threads[:min(limit // len(forum_urls), 10)]:
                                thread_url = thread.get('href', '')
                                if thread_url:
                                    full_url = f"https://forum.imobiliare.ro{thread_url}" if thread_url.startswith('/') else thread_url
                                    context = await self._collect_imobiliare_thread(full_url)
                                    if context:
                                        contexts.append(context)
                                        
                                if len(contexts) >= limit:
                                    break
                
                time.sleep(1)
            
            except Exception as e:
                print(f"Error collecting from Imobiliare.ro {url}: {e}")
                continue
        
        print(f"[DEBUG] Imobiliare.ro collection complete: {len(contexts)} contexts collected")
        return contexts
    
    async def _collect_imobiliare_thread(self, url: str) -> Optional[RedditContext]:
        """Colectează un thread Imobiliare.ro"""
        try:
            headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        title_elem = soup.find('h1') or soup.find('title')
                        title = title_elem.get_text(strip=True) if title_elem else "No title"
                        
                        content_elem = soup.find('div', class_=re.compile(r'post|content|message|discutie'))
                        content = content_elem.get_text(strip=True) if content_elem else ""
                        
                        if len(content) < 50:
                            return None
                        
                        comments = []
                        reply_elems = soup.find_all('div', class_=re.compile(r'reply|comment|post|raspuns'))
                        for reply in reply_elems[:10]:
                            reply_text = reply.get_text(strip=True)
                            if reply_text and len(reply_text) > 20:
                                comments.append({"text": reply_text})
                        
                        return RedditContext(
                            post_id=url.split('/')[-1] or "unknown",
                            post_title=title,
                            post_text=content,
                            post_author=None,
                            post_timestamp=time.time(),
                            post_upvotes=0,
                            subreddit="imobiliare",
                            comments=comments,
                            metadata={"source": "imobiliare", "url": url}
                        )
        
        except Exception as e:
            print(f"Error collecting Imobiliare.ro thread {url}: {e}")
            return None
    
    async def _collect_trustpilot(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează review-uri negative de pe Trustpilot (UK)"""
        contexts = []
        
        categories = ["banks", "insurance", "online-stores"]
        
        headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
        
        for category in categories[:3]:
            try:
                await self.rate_limiter.wait_if_needed()
                
                search_url = f"https://www.trustpilot.com/categories/{category}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            company_links = soup.find_all('a', href=re.compile(r'/review/'))
                            
                            for link in company_links[:min(limit // len(categories), 5)]:
                                company_url = link.get('href', '')
                                if company_url:
                                    full_url = f"https://www.trustpilot.com{company_url}" if company_url.startswith('/') else company_url
                                    review_contexts = await self._collect_trustpilot_reviews(full_url, min_rating=2)
                                    contexts.extend(review_contexts)
                                    
                                if len(contexts) >= limit:
                                    break
                
                time.sleep(2)
        
            except Exception as e:
                print(f"Error collecting from Trustpilot {category}: {e}")
                continue
        
        print(f"[DEBUG] Trustpilot collection complete: {len(contexts)} contexts collected")
        return contexts
    
    async def _collect_trustpilot_reviews(self, company_url: str, min_rating: int = 2) -> List[RedditContext]:
        """Colectează review-uri negative de pe o pagină Trustpilot"""
        contexts = []
        
        try:
            headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(company_url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        reviews = soup.find_all('div', class_=re.compile(r'review|rating'))
                        
                        for review in reviews[:5]:
                            review_text_elem = review.find('p') or review.find('div', class_=re.compile(r'text|content'))
                            review_text = review_text_elem.get_text(strip=True) if review_text_elem else ""
                            
                            if len(review_text) > 50:
                                title_elem = review.find('h2') or review.find('h3')
                                title = title_elem.get_text(strip=True) if title_elem else review_text[:100]
                                
                                contexts.append(RedditContext(
                                    post_id=f"trustpilot_{len(contexts)}",
                                    post_title=title,
                                    post_text=review_text,
                                    post_author=None,
                                    post_timestamp=time.time(),
                                    post_upvotes=0,
                                    subreddit="trustpilot",
                                    comments=[],
                                    metadata={"source": "trustpilot", "url": company_url, "type": "negative_review"}
                                ))
        
        except Exception as e:
            print(f"Error collecting Trustpilot reviews {company_url}: {e}")
        
        return contexts
    
    async def _collect_petitiideclic(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează de pe Petiții Declic (România)"""
        contexts = []
        
        # Petiții Declic URLs
        urls = [
            "https://www.declic.ro/petitii",  # Cele mai recente
            "https://www.declic.ro/petitii?sort=popular",  # Populare
            "https://www.declic.ro/petitii?sort=recent"  # Recente
        ]
        
        headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
        
        for url in urls[:2]:  # Limit to 2 pages
            try:
                await self.rate_limiter.wait_if_needed()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find petition links
                            petition_links = soup.find_all('a', href=re.compile(r'/petitie/|/petitii/'))
                            
                            for link in petition_links[:min(limit // len(urls), 15)]:
                                petition_url = link.get('href', '')
                                if petition_url:
                                    full_url = f"https://www.declic.ro{petition_url}" if petition_url.startswith('/') else petition_url
                                    context = await self._collect_petitiideclic_petition(full_url)
                                    if context:
                                        contexts.append(context)
                                        
                                if len(contexts) >= limit:
                                    break
                
                time.sleep(2)  # Be respectful
            
            except Exception as e:
                print(f"Error collecting from Petiții Declic {url}: {e}")
                continue
        
        print(f"[DEBUG] Petitii Declic collection complete: {len(contexts)} contexts collected")
        return contexts
    
    async def _collect_petitiideclic_petition(self, url: str) -> Optional[RedditContext]:
        """Colectează o petiție Declic"""
        try:
            headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract title
                        title_elem = soup.find('h1') or soup.find('title')
                        title = title_elem.get_text(strip=True) if title_elem else "No title"
                        
                        # Extract description
                        desc_elem = soup.find('div', class_=re.compile(r'description|content|text'))
                        if not desc_elem:
                            desc_elem = soup.find('p')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        # Extract signatures count (validation metric)
                        signatures = 0
                        sig_elem = soup.find(string=re.compile(r'semnături|semnatari'))
                        if sig_elem:
                            sig_text = sig_elem.parent.get_text() if hasattr(sig_elem, 'parent') else str(sig_elem)
                            sig_match = re.search(r'(\d+[\.,]?\d*)', sig_text)
                            if sig_match:
                                try:
                                    signatures = int(sig_match.group(1).replace('.', '').replace(',', ''))
                                except:
                                    pass
                        
                        if len(description) < 50:
                            return None
                        
                        # Combine title and description
                        full_text = f"{title}\n\n{description}"
                        
                        return RedditContext(
                            post_id=url.split('/')[-1] or "unknown",
                            post_title=title,
                            post_text=full_text,
                            post_author=None,
                            post_timestamp=time.time(),
                            post_upvotes=signatures,  # Use signatures as upvotes
                            subreddit="petitiideclic",
                            comments=[],
                            metadata={
                                "source": "petitiideclic",
                                "url": url,
                                "signatures": signatures,
                                "type": "petition"
                            }
                        )
        
        except Exception as e:
            print(f"Error collecting Petiții Declic petition {url}: {e}")
            return None
    
    async def _collect_undelucram(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează recenzii negative de pe Undelucram.ro (România)"""
        contexts = []
        
        # Undelucram.ro - Categorii cu recenzii negative
        categories = [
            "curierat", "retail", "banci", "telecom", "it-software"
        ]
        
        headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
        
        for category in categories[:3]:  # Limit to 3 categories
            try:
                await self.rate_limiter.wait_if_needed()
                
                # Search for companies in category
                search_url = f"https://www.undelucram.ro/cauta/{category}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find company review pages
                            company_links = soup.find_all('a', href=re.compile(r'/companie/|/firma/'))
                            
                            for link in company_links[:min(limit // len(categories), 5)]:
                                company_url = link.get('href', '')
                                if company_url:
                                    full_url = f"https://www.undelucram.ro{company_url}" if company_url.startswith('/') else company_url
                                    # Get negative reviews (1-2 stars)
                                    review_contexts = await self._collect_undelucram_reviews(full_url, min_rating=2)
                                    contexts.extend(review_contexts)
                                    
                                if len(contexts) >= limit:
                                    break
                
                time.sleep(2)  # Be respectful
        
            except Exception as e:
                print(f"Error collecting from Undelucram.ro {category}: {e}")
                continue
        
        print(f"[DEBUG] Undelucram.ro collection complete: {len(contexts)} contexts collected")
        return contexts
    
    async def _collect_undelucram_reviews(self, company_url: str, min_rating: int = 2) -> List[RedditContext]:
        """Colectează review-uri negative de pe o pagină Undelucram.ro"""
        contexts = []
        
        try:
            headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(company_url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find negative reviews (1-2 stars)
                        reviews = soup.find_all('div', class_=re.compile(r'review|rating|comment'))
                        
                        for review in reviews[:5]:  # Limit to 5 reviews per company
                            # Extract review text
                            review_text_elem = review.find('p') or review.find('div', class_=re.compile(r'text|content|comment'))
                            review_text = review_text_elem.get_text(strip=True) if review_text_elem else ""
                            
                            if len(review_text) > 50:  # Only substantial reviews
                                # Extract title if available
                                title_elem = review.find('h2') or review.find('h3') or review.find('strong')
                                title = title_elem.get_text(strip=True) if title_elem else review_text[:100]
                                
                                # Extract company name from URL
                                company_name = company_url.split('/')[-1] or "unknown"
                                
                                contexts.append(RedditContext(
                                    post_id=f"undelucram_{len(contexts)}",
                                    post_title=f"{company_name}: {title}",
                                    post_text=review_text,
                                    post_author=None,
                                    post_timestamp=time.time(),
                                    post_upvotes=0,
                                    subreddit="undelucram",
                                    comments=[],
                                    metadata={
                                        "source": "undelucram",
                                        "url": company_url,
                                        "type": "negative_review",
                                        "company": company_name
                                    }
                                ))
        
        except Exception as e:
            print(f"Error collecting Undelucram.ro reviews {company_url}: {e}")
        
        return contexts
    
    async def _collect_anpc(
        self,
        filters: Optional[Dict],
        limit: int
    ) -> List[RedditContext]:
        """Colectează comunicate ANPC (România)"""
        contexts = []
        
        # ANPC comunicate URLs
        urls = [
            "https://anpc.ro/comunicate-presa",
            "https://anpc.ro/comunicate-presa?page=2"
        ]
        
        headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
        
        for url in urls[:2]:
            try:
                await self.rate_limiter.wait_if_needed()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find communication links
                            comm_links = soup.find_all('a', href=re.compile(r'/comunicat/|/comunicate/'))
                            
                            for link in comm_links[:min(limit // len(urls), 10)]:
                                comm_url = link.get('href', '')
                                if comm_url:
                                    full_url = f"https://anpc.ro{comm_url}" if comm_url.startswith('/') else comm_url
                                    context = await self._collect_anpc_communication(full_url)
                                    if context:
                                        contexts.append(context)
                                        
                                if len(contexts) >= limit:
                                    break
                
                time.sleep(2)  # Be respectful
            
            except Exception as e:
                print(f"Error collecting from ANPC {url}: {e}")
                continue
        
        print(f"[DEBUG] ANPC collection complete: {len(contexts)} contexts collected")
        return contexts
    
    async def _collect_anpc_communication(self, url: str) -> Optional[RedditContext]:
        """Colectează un comunicat ANPC"""
        try:
            headers = {"User-Agent": "WishCatcher/1.0 (Educational Research)"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract title
                        title_elem = soup.find('h1') or soup.find('title')
                        title = title_elem.get_text(strip=True) if title_elem else "No title"
                        
                        # Extract content
                        content_elem = soup.find('div', class_=re.compile(r'content|article|text'))
                        if not content_elem:
                            content_elem = soup.find('article')
                        content = content_elem.get_text(strip=True) if content_elem else ""
                        
                        # Extract fine amount if mentioned (indicator of severity)
                        fine = 0
                        fine_match = re.search(r'(\d+[\.,]?\d*)\s*(?:lei|RON|EUR)', content, re.IGNORECASE)
                        if fine_match:
                            try:
                                fine = int(fine_match.group(1).replace('.', '').replace(',', ''))
                            except:
                                pass
                        
                        if len(content) < 50:
                            return None
                        
                        return RedditContext(
                            post_id=url.split('/')[-1] or "unknown",
                            post_title=title,
                            post_text=content,
                            post_author=None,
                            post_timestamp=time.time(),
                            post_upvotes=fine,  # Use fine amount as upvotes (indicator of problem severity)
                            subreddit="anpc",
                            comments=[],
                            metadata={
                                "source": "anpc",
                                "url": url,
                                "fine_amount": fine,
                                "type": "official_communication"
                            }
                        )
        
        except Exception as e:
            print(f"Error collecting ANPC communication {url}: {e}")
            return None


class RateLimiter:
    """Rate limiter pentru requests"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def wait_if_needed(self):
        """Așteaptă dacă e necesar"""
        now = time.time()
        
        # Remove old requests
        self.requests = [r for r in self.requests if r > now - self.time_window]
        
        # Wait if needed
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                self.requests = [r for r in self.requests if r > now - self.time_window]
        
        self.requests.append(time.time())
