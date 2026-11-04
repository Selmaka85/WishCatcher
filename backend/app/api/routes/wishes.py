"""
WishCatcher API Routes
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from app.api.models import (
    WishRequest, WishResponse, WishData,
    ComplementarityRequest, ComplementarityResponse
)
from app.wishcatcher.scraper.context_collector import ContextCollector
from app.wishcatcher.parser.robust_intent_detector import RobustIntentDetector
from app.wishcatcher.parser.intent_reformulator import IntentReformulator
from app.wishcatcher.validator.reality_checker import RealityChecker
from app.wishcatcher.trigger_analyzer.trigger_analyzer import TriggerAnalyzer
from app.wishcatcher.clusterer.complementarity_detector import ComplementarityDetector
from app.wishcatcher.scorer.business_scorer import BusinessScorer
# Noi detectoare proactivi
from app.wishcatcher.detector.proactive_wish_detector import ProactiveWishDetector
from app.wishcatcher.detector.implicit_intent_detector import ImplicitIntentDetector
from app.wishcatcher.detector.conversational_analyzer import ConversationalAnalyzer
from app.wishcatcher.detector.workaround_detector import WorkaroundDetector
from app.wishcatcher.detector.comparison_analyzer import ComparisonAnalyzer
# Analizatori și prioritizare
from app.wishcatcher.analyzer.market_research_validator import MarketResearchValidator
from app.wishcatcher.analyzer.feedback_loop import FeedbackLoop
from app.wishcatcher.prioritizer.smart_prioritizer import SmartPrioritizer
from app.wishcatcher.extractor.precise_context_extractor import PreciseContextExtractor
from app.wishcatcher.contextual.context_resolver import ConversationContextResolver
from app.storage.wish_storage import WishStorage
from app.product_gaps.auto_gap_finder import AutoGapFinder
from app.storage.product_gap_storage import ProductGapStorage
# Software Gap Finder (import în funcție pentru a evita erori la startup)
# from app.software_gaps.software_gap_finder import SoftwareGapFinder
# from app.software_gaps.storage.software_gap_storage import SoftwareGapStorage
from datetime import datetime

router = APIRouter()

# Inițializează storage
wish_storage = WishStorage()


@router.post("/collect", response_model=WishResponse)
async def collect_wishes(
    request: WishRequest,
    background_tasks: BackgroundTasks
):
    import time
    start_time = time.time()
    """
    Colectează dorințe din surse specificate
    
    - **sources**: Lista de surse (reddit, quora, gumtree, etc.)
    - **filters**: Filtre geografice/culturale
    - **limit**: Număr maxim de wish-uri de colectat
    """
    # Debug logging
    print(f"[DEBUG] Received request: sources={request.sources}, limit={request.limit}, filters={request.filters}")
    
    try:
        # Initialize collectors
        collector = ContextCollector()
        
        # Collect context from sources
        all_contexts = []
        for source in request.sources:
            print(f"[DEBUG] Collecting from {source}...")
            try:
                contexts = await collector.collect_from_source(
                    source=context_source,
                    filters=request.filters,
                    limit=request.limit // len(request.sources)
                )
                print(f"[DEBUG] Collected {len(contexts)} contexts from {source}")
                all_contexts.extend((source, collected_context) for collected_context in contexts)
            except Exception as e:
                print(f"[ERROR] Error collecting from {source}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"[DEBUG] Total contexts collected: {len(all_contexts)}")
        
        # Process contexts
        intent_detector = RobustIntentDetector()
        intent_reformulator = IntentReformulator()
        reality_checker = RealityChecker()
        trigger_analyzer = TriggerAnalyzer()
        scorer = BusinessScorer()
        
        # Noi detectoare proactivi
        proactive_detector = ProactiveWishDetector()
        implicit_detector = ImplicitIntentDetector()
        conversational_analyzer = ConversationalAnalyzer()
        workaround_detector = WorkaroundDetector()
        comparison_analyzer = ComparisonAnalyzer()
        
        # Analizatori și prioritizare
        market_validator = MarketResearchValidator()
        feedback_loop = FeedbackLoop()
        smart_prioritizer = SmartPrioritizer()
        
        # Extragere precisă de context (ca ChatGPT/Google)
        precise_extractor = PreciseContextExtractor()
        contextual_resolver = ConversationContextResolver()
        
        wishes = []
        contexts_processed = 0
        contexts_with_intent = 0
        contexts_filtered = 0  # Wish-uri filtrate ca nonsens
        proactive_wishes = 0  # Wish-uri detectate proactiv
        implicit_wishes = 0  # Wish-uri implicite detectate
        
        print(f"[DEBUG] Processing {len(all_contexts)} contexts...")
        
        # Get language filter from request
        language_filter = None
        if request.filters and request.filters.get("language"):
            language_filter = request.filters.get("language")
            print(f"[DEBUG] Language filter: {language_filter}")
        
        for context_source, context in all_contexts:
            contexts_processed += 1
            try:
                # Reconstruct the original speaker's need from the FULL thread first.
                # Never discard a vague opening post before reading its clarifications.
                raw_context = context.to_dict()
                context_frame = await contextual_resolver.resolve(raw_context)
                contextual_intent = bool(context_frame.actionable and context_frame.confidence >= 0.5)
                intent_data = intent_detector.detect_intent(
                    text=context.post_text,
                    context=raw_context
                )
                if contextual_intent and (not intent_data.get("intent") or context_frame.interpretation_method == "llm_contextual"):
                    intent_data = {
                        **intent_data,
                        "intent": context_frame.intent,
                        "confidence": context_frame.confidence,
                        "language": context_frame.language,
                        "domain": context_frame.domain,
                    }
                
                # Filter by language if specified
                detected_language = intent_data.get("language", "unknown")
                if language_filter and language_filter != "all":
                    if detected_language != language_filter:
                        if contexts_processed % 20 == 0:
                            print(f"[DEBUG] Skipped context (language mismatch: {detected_language} != {language_filter})")
                        continue
                
                # Acceptă wish-uri cu intent detectat, chiar dacă confidence e scăzut
                # Threshold minim: 0.3 (foarte permisiv pentru colectare)
                intent = intent_data.get("intent")
                confidence = intent_data.get("confidence", 0.0)
                
                if (not intent or confidence < 0.3) and not contextual_intent:
                    if contexts_processed % 10 == 0:
                        print(f"[DEBUG] Skipped {contexts_processed} contexts, found {contexts_with_intent} with intent")
                    continue
                
                # NOU: Extragere precisă de context (ca ChatGPT/Google) - filtrează garbage-ul
                precise_context = precise_extractor.extract_precise_context(
                    text=context.post_text,
                    language=detected_language,
                    context=context.to_dict()
                )
                
                # Dacă nu e valid (garbage), skip
                if (not precise_context or not precise_context.get("is_valid", False)) and not contextual_intent:
                    contexts_filtered += 1
                    rejection_reason = precise_context.get("rejection_reason", "Not specific enough") if precise_context else "No precise context"
                    if contexts_filtered % 10 == 0:
                        print(f"[DEBUG] Filtered {contexts_filtered} wishes (precise context: {rejection_reason})")
                    continue
                
                # Dacă specificitatea sau relevanța e prea scăzută, skip
                specificity = precise_context.get("specificity_score", 0.0)
                relevance = precise_context.get("relevance_score", 0.0)
                if (specificity < 0.5 or relevance < 0.5) and not contextual_intent:
                    contexts_filtered += 1
                    if contexts_filtered % 10 == 0:
                        print(f"[DEBUG] Filtered {contexts_filtered} wishes (specificity: {specificity:.2f}, relevance: {relevance:.2f})")
                    continue
                
                contexts_with_intent += 1
                print(f"[DEBUG] Found valid intent in {detected_language}: {intent[:50]}... (specificity: {specificity:.2f}, relevance: {relevance:.2f})")
                
                # Detectează wish-uri proactivi (din pattern-uri de frustrare/eșec)
                proactive_wish = proactive_detector.detect_proactive_wish(
                    text=context.post_text,
                    language=detected_language,
                    context=context.to_dict()
                )
                
                # Detectează wish-uri implicite (din acțiuni)
                implicit_wish = implicit_detector.detect_implicit_wish(
                    text=context.post_text,
                    language=detected_language,
                    context=context.to_dict()
                )
                
                # Analizează conversația completă (post + comentarii)
                conversational_wish = conversational_analyzer.analyze_conversation(
                    post_text=context.post_text,
                    comments=context.comments if hasattr(context, 'comments') else [],
                    language=detected_language
                )
                
                # Detectează wish-uri din workaround-uri
                workaround_wish = workaround_detector.detect_workaround_wish(
                    text=context.post_text,
                    language=detected_language
                )
                
                # Analizează comparații pentru wish-uri
                comparison_wish = comparison_analyzer.analyze_comparison(
                    text=context.post_text,
                    language=detected_language
                )
                
                # Alege wish-ul cel mai bun (prioritizează wish-uri proactivi/implicite)
                final_intent = intent
                if workaround_wish and workaround_wish.get("confidence", 0) > 0.8:
                    final_intent = workaround_wish.get("wish", intent)
                    proactive_wishes += 1
                    print(f"[DEBUG] Workaround wish detected: {final_intent[:50]}...")
                elif proactive_wish and proactive_wish.get("confidence", 0) > 0.7:
                    final_intent = proactive_wish.get("wish", intent)
                    proactive_wishes += 1
                    print(f"[DEBUG] Proactive wish detected: {final_intent[:50]}...")
                elif implicit_wish and implicit_wish.get("confidence", 0) > 0.7:
                    final_intent = implicit_wish.get("wish", intent)
                    implicit_wishes += 1
                    print(f"[DEBUG] Implicit wish detected: {final_intent[:50]}...")
                elif conversational_wish and conversational_wish.get("confidence", 0) > 0.7:
                    final_intent = conversational_wish.get("wish", intent)
                    print(f"[DEBUG] Conversational wish detected: {final_intent[:50]}...")
                elif comparison_wish and comparison_wish.get("confidence", 0) > 0.7:
                    final_intent = comparison_wish.get("wish", intent)
                    print(f"[DEBUG] Comparison wish detected: {final_intent[:50]}...")
                
                # A contextual reconstruction of the whole thread takes precedence
                # over a regex fragment, while the original detectors stay active.
                if contextual_intent:
                    final_intent = context_frame.intent

                # Validate the ACTUAL selected intent, not an earlier fragment.
                is_valid, validation_reason, validation_confidence = reality_checker.validate_wish(
                    intent=final_intent,
                    language=detected_language,
                    context=raw_context,
                )
                if not is_valid:
                    contexts_filtered += 1
                    continue

                # Analyze triggers with the resolved intent and original provenance.
                trigger_data = trigger_analyzer.analyze(
                    text=final_intent,
                    full_context=raw_context,
                )
                
                # Reformulate intent (construiește structură completă)
                # Folosește final_intent (poate fi din detectoare proactivi)
                reformulated = intent_reformulator.reformulate_intent(
                    intent=final_intent,  # Folosește wish-ul final (proactiv/implicit/etc)
                    language=detected_language,
                    context={**raw_context, "context_frame": context_frame.to_dict()},
                    trigger_analysis=trigger_data
                )
                if contextual_intent:
                    structured = reformulated.setdefault("structured", {})
                    structured.update({
                        "problem": context_frame.problem,
                        "desired_outcome": context_frame.desired_outcome,
                        "constraints": context_frame.constraints,
                        "attempted_solutions": context_frame.attempted_solutions,
                        "rejected_alternatives": context_frame.rejected_alternatives,
                        "evidence": context_frame.evidence,
                        "epistemic_status": context_frame.epistemic_status,
                    })
                    reformulated["intent_short"] = final_intent[:500]
                    reformulated["intent_full"] = (
                        f"Problem: {context_frame.problem}. "
                        f"Desired outcome: {context_frame.desired_outcome}. "
                        f"Resolved intent: {final_intent}"
                    )
                
                # Calculate business score
                # Adaugă informații precise extrase
                precise_info = precise_context.get("extracted_context", {})
                wish_data = {
                    "intent": final_intent,  # Folosește wish-ul final
                    "intent_short": reformulated.get("intent_short", final_intent),
                    "intent_full": reformulated.get("intent_full", final_intent),
                    "structured": reformulated.get("structured", {}),
                    "domain": intent_data.get("domain", "other"),
                    "trigger_analysis": trigger_data,
                    "source": context_source,
                    "context": raw_context,
                    "context_frame": context_frame.to_dict(),
                    "frequency": 1,  # Will be updated after clustering
                    # Informații precise extrase
                    "precise_context": {
                        "entity_type": precise_context.get("entity_type", "unknown"),
                        "entity_name": precise_context.get("entity_name", ""),
                        "category": precise_context.get("category", ""),
                        "functionality": precise_context.get("functionality", ""),
                        "specificity_score": precise_context.get("specificity_score", 0.0),
                        "relevance_score": precise_context.get("relevance_score", 0.0),
                        "keywords": precise_info.get("keywords", []),
                        "intent_indicators": precise_info.get("intent_indicators", [])
                    }
                }
                
                business_score = scorer.calculate_business_score(wish_data)
                
                # Validare market research (dacă e disponibil)
                market_validation = market_validator.validate_wish(
                    wish=final_intent,
                    language=detected_language,
                    country="RO" if detected_language == "ro" else "UK"
                )
                
                # Smart prioritization
                prioritization = smart_prioritizer.prioritize(
                    wish_data=wish_data,
                    context=context.to_dict()
                )
                
                # Ajustează business score cu feedback loop
                adjusted_score = feedback_loop.adjust_scoring(wish_data)
                if adjusted_score != business_score:
                    business_score = adjusted_score
                    print(f"[DEBUG] Adjusted business score from {business_score:.2f} to {adjusted_score:.2f} based on feedback")
                
                # Create wish data (folosim intent_short pentru afișare, intent_full pentru detalii)
                wish = WishData(
                    id=f"wish_{len(wishes)}_{datetime.now().timestamp()}",
                    intent=reformulated.get("intent_short", final_intent),  # Afișare: intent_short
                    domain=intent_data.get("domain", "other"),
                    score=intent_data.get("confidence", 0.5),
                    business_score=business_score,
                    technologies=intent_data.get("technologies", []),
                    feasibility=scorer.get_feasibility(wish_data),
                    trigger_analysis=trigger_data,
                    source=source,
                    timestamp=datetime.fromtimestamp(context.post_timestamp) if hasattr(context, 'post_timestamp') and context.post_timestamp else datetime.now(),
                    frequency=1,
                    context_frame=context_frame.to_dict(),
                    market_analysis=scorer.get_market_analysis(wish_data),
                    monetization=scorer.get_monetization_analysis(wish_data)
                )
                
                # Adaugă date de prioritizare și validare market
                wish_dict = wish.model_dump()
                wish_dict["priority_score"] = prioritization.get("priority_score", 0.5)
                wish_dict["urgency"] = prioritization.get("urgency", "medium")
                wish_dict["timing"] = prioritization.get("timing", "later")
                wish_dict["market_readiness"] = prioritization.get("market_readiness", "not_ready")
                wish_dict["market_validation"] = market_validation
                wish = WishData(**wish_dict)
                
                # Adaugă câmpurile reformulate la wish (vor fi salvate în storage)
                wish_dict = wish.model_dump()
                wish_dict["intent_full"] = reformulated.get("intent_full", "")
                wish_dict["structured"] = reformulated.get("structured", {})
                # Actualizează wish cu datele complete
                wish = WishData(**wish_dict)
                
                wishes.append(wish)
            except Exception as e:
                print(f"[ERROR] Error processing context {contexts_processed}: {e}")
                import traceback
                traceback.print_exc()
                # Continuă procesarea altor contexte chiar dacă unul eșuează
                continue
        
        print(f"[DEBUG] Final stats: {contexts_processed} contexts processed, {contexts_with_intent} with intent, {contexts_filtered} filtered (nonsens/imposibil), {proactive_wishes} proactive wishes, {implicit_wishes} implicit wishes, {len(wishes)} wishes created")
        
        # Salvează wish-uri în storage
        if wishes:
            wish_storage.save_wishes(wishes)
            print(f"[DEBUG] Saved {len(wishes)} wishes to storage")
            
            # Procesează automat gap-uri pentru produse fizice (background task)
            async def process_gaps_async():
                try:
                    auto_gap_finder = AutoGapFinder()
                    gap_storage = ProductGapStorage()
                    
                    # Convertește wish-uri la dict pentru procesare
                    wish_dicts = []
                    for w in wishes:
                        try:
                            if hasattr(w, 'model_dump'):
                                wish_dict = w.model_dump()
                            elif hasattr(w, 'dict'):
                                wish_dict = w.dict()
                            elif hasattr(w, '__dict__'):
                                wish_dict = w.__dict__.copy()
                            elif isinstance(w, dict):
                                wish_dict = w.copy()
                            else:
                                # Try Pydantic model conversion
                                wish_dict = dict(w)
                            
                            # Asigură-te că toate câmpurile necesare sunt prezente
                            if 'id' in wish_dict and 'intent' in wish_dict:
                                wish_dicts.append(wish_dict)
                        except Exception as e:
                            print(f"[WARNING] Could not convert wish to dict: {e}")
                            import traceback
                            traceback.print_exc()
                            continue
                    
                    if wish_dicts:
                        # Procesează gap-uri
                        gaps = await auto_gap_finder.process_wish_batch(wish_dicts)
                        
                        if gaps:
                            saved_count = gap_storage.save_gaps(gaps)
                            print(f"[AutoGapFinder] Saved {saved_count} new gaps from {len(wish_dicts)} wishes")
                    else:
                        print(f"[AutoGapFinder] No valid wishes to process for gaps")
                except Exception as e:
                    print(f"[ERROR] Error processing gaps automatically: {e}")
                    import traceback
                    traceback.print_exc()
                    # Nu aruncă eroarea - doar loghează pentru a nu afecta răspunsul principal
            
            # Procesează automat gap-uri pentru software/servicii (background task)
            async def process_software_gaps_async():
                try:
                    try:
                        from app.software_gaps.software_gap_finder import SoftwareGapFinder
                        from app.software_gaps.storage.software_gap_storage import SoftwareGapStorage
                    except ImportError as import_err:
                        print(f"[ERROR] Could not import SoftwareGapFinder modules: {import_err}")
                        import traceback
                        traceback.print_exc()
                        return  # Exit early if imports fail
                    
                    software_gap_finder = SoftwareGapFinder()
                    software_gap_storage = SoftwareGapStorage()
                    
                    # Convertește wish-uri la dict pentru procesare
                    wish_dicts = []
                    for w in wishes:
                        try:
                            if hasattr(w, 'model_dump'):
                                wish_dict = w.model_dump()
                            elif hasattr(w, 'dict'):
                                wish_dict = w.dict()
                            elif hasattr(w, '__dict__'):
                                wish_dict = w.__dict__.copy()
                            elif isinstance(w, dict):
                                wish_dict = w.copy()
                            else:
                                wish_dict = dict(w)
                            
                            wish_dicts.append(wish_dict)
                        except Exception as e:
                            print(f"[WARNING] Could not convert wish to dict for software gaps: {e}")
                            import traceback
                            traceback.print_exc()
                            continue
                    
                    if wish_dicts:
                        software_gaps = await software_gap_finder.process_wish_batch(wish_dicts)
                        if software_gaps:
                            saved_count = software_gap_storage.save_gaps(software_gaps)
                            print(f"[SoftwareGapFinder] Saved {saved_count} new software gaps from {len(wish_dicts)} wishes")
                    else:
                        print(f"[SoftwareGapFinder] No valid wishes to process for software gaps")
                except Exception as e:
                    print(f"[ERROR] Error in background software gap processing: {e}")
                    import traceback
                    traceback.print_exc()
                    # Nu aruncă eroarea - doar loghează pentru a nu afecta răspunsul principal
            
            # Rulează în background (non-blocking) - nu blochează răspunsul
            try:
                background_tasks.add_task(process_gaps_async)
            except Exception as e:
                print(f"[WARNING] Could not add product gaps background task: {e}")
                import traceback
                traceback.print_exc()
            
            try:
                background_tasks.add_task(process_software_gaps_async)
            except Exception as e:
                print(f"[WARNING] Could not add software gaps background task: {e}")
                import traceback
                traceback.print_exc()
        
        processing_time = time.time() - start_time
        
        return WishResponse(
            wishes=wishes,
            total=len(wishes),
            sources_used=request.sources,
            processing_time=round(processing_time, 2),
            filters_applied=request.filters or {}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error in collect_wishes endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/combine", response_model=ComplementarityResponse)
async def combine_wishes(request: ComplementarityRequest):
    """
    Combină dorințe complementare (N flexibil)
    
    - **wish_ids**: Lista de ID-uri de wish-uri de combinat
    - **min_similarity**: Similaritate minimă (0.7 default)
    - **max_wishes**: Număr maxim de wish-uri de combinat (7 default)
    """
    try:
        detector = ComplementarityDetector()
        
        # Get wishes (ar trebui să fie din DB, aici simplificat)
        # TODO: Load wishes from database
        
        result = await detector.detect_complementarity(
            wish_ids=request.wish_ids,
            min_similarity=request.min_similarity,
            max_wishes=request.max_wishes
        )
        
        return ComplementarityResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{wish_id}", response_model=WishData)
async def get_wish(wish_id: str):
    """Obține un wish specific"""
    wish = wish_storage.get_wish(wish_id)
    if not wish:
        raise HTTPException(status_code=404, detail="Wish not found")
    return wish


@router.get("/", response_model=List[WishData])
async def list_wishes(
    limit: int = 100, 
    offset: int = 0,
    source: Optional[str] = None,
    domain: Optional[str] = None
):
    """Listează wish-uri (cu paginare și filtre)"""
    return wish_storage.list_wishes(limit=limit, offset=offset, source=source, domain=domain)
