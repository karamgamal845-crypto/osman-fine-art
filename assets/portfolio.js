        function osmanArt() {
            return {
                lang: localStorage.getItem('osman_lang') || 'en', view: 'site', loading: true, mobileMenu: false, showModal: false, zoom: false, selectedArt: null, visitorMessage: '', artworks: [],
                get galleryArtworks() { return this.artworks.filter(art => art.type !== 'about' && art.type !== 'archive'); },
                filterType: 'all',
                get categories() { return [...new Set(this.galleryArtworks.map(a => a.type || 'gallery'))]; },
                get visibleArtworks() { return this.filterType === 'all' ? this.galleryArtworks : this.galleryArtworks.filter(a => (a.type || 'gallery') === this.filterType); },
                categoryName(k) { const n={all:['All works','كل الأعمال'],gallery:['Paintings','لوحات'],more:['More works','أعمال أخرى'],drawing:['Drawings','رسومات'],wall:['Wall work','أعمال جدارية'],ceramics:['Ceramics','خزف']}; return (n[k]||[k,k])[this.lang==='ar'?1:0]; },
                get featuredWorks() { return this.galleryArtworks.filter(a=>a.featured); },
                get latestWorks() { return this.galleryArtworks.filter(a => a.type && a.type !== 'gallery').slice(-4).reverse(); },
                pages: {}, thumbs: {}, fulls: {}, sizes: {},
                imageSize(a) { return this.sizes[a?.id] || {w:600,h:800}; },
                full(a) { return (a && this.fulls[a.id]) || (a && a.image) || ''; },
                imgFallback(e) { const a = this.selectedArt; if (a && a.image && e.target.getAttribute('src') !== a.image) e.target.src = a.image; },
                thumb(a) { return this.thumbs[a.id] || a.image; },
                pageUrl(a) { const p = this.pages[a.id]; return p ? p : ''; },
                get aboutArtworks() { return this.artworks.filter(art => art.type === 'about'); },
                commForm: { name: '', email: '', subject: '', vision: '' },
                init() { this.loadArtworks();  },
                t(key) { return TRANSLATIONS[this.lang][key] || key; },
                displayTitle(art) {
                    if (!art) return '';
                    if (this.lang !== 'ar') return art.title;
                    const names = { '1': 'عالم آخر', '3': 'سيمفونية الطيور', '4': 'الطاووس', '5': 'الفلوكة', '6': 'ليوناردو دافنشي', '7': 'جوستاف كوربيه II', '8': 'هنري ماتيس', '9': 'كلود مونيه', '10': 'جوستاف كوربيه I', '12': 'رجل مع غراب' };
                    return names[art.id] || art.title_ar || (art.title === 'Artwork (details pending)' ? 'عمل فني (التفاصيل قريبًا)' : art.title);
                },
                groupLabel(idx) {
                    const art = this.visibleArtworks[idx], prev = this.visibleArtworks[idx - 1];
                    if (!art || !art.type || art.type === 'gallery' || (prev && prev.type === art.type)) return '';
                    const labels = { more: ['More works', 'أعمال أخرى'], drawing: ['Drawings', 'رسومات'], wall: ['Wall work', 'أعمال جدارية'], ceramics: ['Ceramics', 'خزف'] };
                    const l = labels[art.type]; return l ? l[this.lang === 'ar' ? 1 : 0] : '';
                },
                displayMedium(art) {
                    if (!art?.medium) return '';
                    if (this.lang !== 'ar') return art.medium;
                    const media = { 'Acrylic on linen fabric': 'أكريليك على قماش كتان', 'Mix Media Acrylic and Embroidery': 'أكريليك وتطريز', 'Faber-Castell on 500gsm paper': 'ألوان فابر كاستل على ورق 500 جرام', 'Faber-Castell colored pencils on 500gsm paper': 'ألوان خشبية فابر كاستل على ورق 500 جرام', 'Oil on canvas': 'ألوان زيتية على قماش' };
                    return media[art.medium] || art.medium;
                },
                displayDescription(art) {
                    if (!art) return '';
                    if (this.lang !== 'ar') return art.description;
                    const descriptions = { '1': 'طيور ونباتات بألوان الأكريليك على الكتان.', '3': 'ألوان أكريليك مع تطريز يدوي.', '4': 'طواويس بألوان الأكريليك على الكتان.', '5': 'مستوحاة من النيل.', '6': 'دراسة معاد رسمها لليوناردو دافنشي. من سلسلة Art Project: رواد المدارس الفنية.', '7': 'رائد المدرسة الواقعية، أعاد رسمه بأسلوبه. من سلسلة Art Project.', '8': 'رائد المدرسة الوحشية، أعاد رسمه بأسلوبه. من سلسلة Art Project.', '9': 'رائد المدرسة الانطباعية، أعاد رسمه بأسلوبه. من سلسلة Art Project.', '10': 'رائد المدرسة الواقعية، أعاد رسمه بأسلوبه. من سلسلة Art Project.', '12': 'أضاف الغراب وهو في حالة تفكير.' };
                    return descriptions[art.id] || art.description;
                },
                displayDimensions(art) { return this.lang === 'ar' ? (art?.dimensions || '').replaceAll('cm', 'سم').replace('circle', 'قطر الدائرة') : art?.dimensions; },
                displayPrice(art) { return this.lang === 'ar' ? (art?.price || '').replace('EGP', 'جنيه') : art?.price; },
                toggleLang() { this.lang = this.lang === 'en' ? 'ar' : 'en'; localStorage.setItem('osman_lang', this.lang); },
                async loadArtworks() {
                    this.loading = true;
                    try {
                        const SHEET_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSiChHx_Y9xUhLWb42AXOVrqUMVSUa-G01laFnTo3IZgE2HLPnUSmpHiZhBy79rluBUyYvshSuCDreI/pub?output=csv';
                        const catalogPromise = fetch('works.json').then(pr => pr.ok ? pr.json() : []).catch(() => []);
                        const response = await fetch(SHEET_URL);
                        if (!response.ok) throw new Error('Artwork sheet unavailable');
                        (await catalogPromise).forEach(w => { this.pages[w.id] = 'work/' + w.slug + '/'; this.thumbs[w.id] = w.thumb; this.fulls[w.id] = w.full; this.sizes[w.id] = {w:w.w,h:w.h}; });
                        const text = await response.text();
                        this.artworks = this.parseCSV(text); const m = location.hash.match(/^#work-(\d+)$/); if (m) { const a = this.artworks.find(x => x.id === m[1]); if (a) setTimeout(() => this.openArt(a), 0); }
                    } catch (e) { console.error('Load artworks failed', e); this.artworks = FALLBACK_ARTWORKS; }
                    this.loading = false;
                },
                parseCSV(text) {
                    const LOGO_URL = 'art/21-logo.jpg';
                    const rows = [];
                    let result = [];
                    let cell = '';
                    let inQuotes = false;
                    
                    for (let i = 0; i < text.length; i++) {
                        const char = text[i];
                        const nextChar = text[i + 1];
                        
                        if (char === '"' && inQuotes && nextChar === '"') {
                            cell += '"';
                            i++;
                        } else if (char === '"') {
                            inQuotes = !inQuotes;
                        } else if (char === ',' && !inQuotes) {
                            result.push(cell.trim());
                            cell = '';
                        } else if ((char === '\n' || char === '\r') && !inQuotes) {
                            if (cell !== '' || result.length > 0) {
                                result.push(cell.trim());
                                rows.push(result);
                                result = [];
                                cell = '';
                            }
                            if (char === '\r' && nextChar === '\n') i++;
                        } else {
                            cell += char;
                        }
                    }
                    if (result.length > 0 || cell !== '') {
                        result.push(cell.trim());
                        rows.push(result);
                    }

                    const header = rows[0].map(h => (h || '').toLowerCase().trim());
                    const col = name => header.indexOf(name);
                    const get = (r, name) => { const i = col(name); return i === -1 ? '' : (r[i] || ''); };
                    return rows.slice(1).map(result => {
                        if (result.length < 7) return null;
                        const art = {
                            id: get(result, 'id'),
                            title: get(result, 'title'),
                            year: get(result, 'year'),
                            medium: get(result, 'medium'),
                            price: get(result, 'price'),
                            dimensions: get(result, 'dimensions'),
                            image: get(result, 'image'),
                            description: get(result, 'description'),
                            status: get(result, 'status').toLowerCase().trim(),
                            type: get(result, 'type').toLowerCase().trim(),
                            title_ar: get(result, 'title_ar'),
                            featured: ['true','1','yes'].includes(get(result,'featured').toLowerCase().trim())
                        };
                        if (art.image === LOGO_URL) return null;
                        return art;
                    }).filter(Boolean);
                },
                closeArt() { this.showModal = false; this.zoom = false; if (location.hash.startsWith('#work-')) try { history.replaceState(null, '', location.pathname); } catch (e) {} },
                step(d) { const l = this.galleryArtworks; if (!l.length) return; const i = l.indexOf(this.selectedArt); this.selectedArt = l[(i + d + l.length) % l.length]; this.visitorMessage = ''; try { history.replaceState(null, '', '#work-' + this.selectedArt.id); } catch (e) {} },
                openArt(art) { this.selectedArt = art; try { history.replaceState(null, '', '#work-' + art.id); } catch (e) {} this.visitorMessage = ''; this.showModal = true; this.$nextTick(() => document.querySelector('[aria-label="Close"]')?.focus()); },
                sendArtInquiry() {
                    const lines = [`مرحباً عثمان، أنا مهتم بعملك الفني: ${this.selectedArt.title}`];
                    if (this.selectedArt.dimensions) lines.push(`الأبعاد: ${this.selectedArt.dimensions}`);
                    if (this.selectedArt.price) lines.push(`السعر: ${this.selectedArt.price}`);
                    if (this.selectedArt.medium) lines.push(`الخامة: ${this.selectedArt.medium}`);
                    const text = lines.join('\n') + `\n\nرسالة من الزائر: ${this.visitorMessage}`;
                    window.open(`https://wa.me/201026933840?text=${encodeURIComponent(text)}`, '_blank');
                },
                sendCommission() {
                    window.location.href = `mailto:osmanrafaat05@gmail.com?subject=${encodeURIComponent(this.commForm.subject)}&body=${encodeURIComponent(`الاسم: ${this.commForm.name}\nالبريد: ${this.commForm.email}\n${this.commForm.vision}`)}`;
                    this.commForm = { name: '', email: '', subject: '', vision: '' };
                }
            }
        }
    
