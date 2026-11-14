# ===== Better terminal search (like in newer AE2 versions) =====
# Terms separated by spaces must all match, "|" separates alternatives.
# Prefixes: @mod  $tooltip  #tag  *item id. Without a prefix the name is searched.
path = 'src/main/java/appeng/client/gui/me/common/Repo.java'
s = open(path).read()
if 'parseSearch' not in s:
    def rep(old, new):
        global s
        assert s.count(old) == 1, 'anchor not found exactly once: ' + old[:80]
        s = s.replace(old, new)

    rep('''        SearchMode searchMode = SearchMode.NAME;
        if (AEConfig.instance().getSearchTooltips() != YesNo.NO) {
            searchMode = SearchMode.NAME_OR_TOOLTIP;
        }

        String innerSearch = this.searchString;
        if (innerSearch.startsWith("@")) {
            searchMode = SearchMode.MOD;
            innerSearch = innerSearch.substring(1);
        }

        Pattern m;
        try {
            m = Pattern.compile(innerSearch.toLowerCase(),
                    Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE);
        } catch (PatternSyntaxException ignored) {
            m = Pattern.compile(Pattern.quote(innerSearch.toLowerCase()),
                    Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE);
        }
''', '''        final java.util.List<java.util.List<SearchTerm>> searchGroups = parseSearch(this.searchString);
''')

    rep('            if (matchesSearch(searchMode, m, entry.getStack())) {\n',
        '            if (matchesParsedSearch(searchGroups, entry.getStack())) {\n')

    rep('    protected abstract boolean matchesSearch(SearchMode searchMode, Pattern searchPattern, T stack);\n',
        '''    private static final class SearchTerm {
        final SearchMode mode;
        final Pattern pattern;
        final String text;
        /**
         * 0 = name/tooltip/mod search, 1 = tag search, 2 = item id search
         */
        final int kind;

        SearchTerm(SearchMode mode, Pattern pattern, String text, int kind) {
            this.mode = mode;
            this.pattern = pattern;
            this.text = text;
            this.kind = kind;
        }
    }

    private static Pattern createPattern(String text) {
        try {
            return Pattern.compile(text, Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE);
        } catch (PatternSyntaxException ignored) {
            return Pattern.compile(Pattern.quote(text), Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE);
        }
    }

    private java.util.List<java.util.List<SearchTerm>> parseSearch(String search) {
        SearchMode defaultMode = SearchMode.NAME;
        if (AEConfig.instance().getSearchTooltips() != YesNo.NO) {
            defaultMode = SearchMode.NAME_OR_TOOLTIP;
        }

        final java.util.List<java.util.List<SearchTerm>> groups = new java.util.ArrayList<>();
        for (String orPart : search.split("\\\\|", -1)) {
            final java.util.List<SearchTerm> terms = new java.util.ArrayList<>();
            final String trimmed = orPart.trim().toLowerCase();
            if (!trimmed.isEmpty()) {
                for (String part : trimmed.split("\\\\s+")) {
                    if (part.startsWith("@")) {
                        terms.add(new SearchTerm(SearchMode.MOD, createPattern(part.substring(1)), "", 0));
                    } else if (part.startsWith("$")) {
                        terms.add(new SearchTerm(SearchMode.NAME_OR_TOOLTIP, createPattern(part.substring(1)), "", 0));
                    } else if (part.startsWith("#")) {
                        terms.add(new SearchTerm(null, null, part.substring(1), 1));
                    } else if (part.startsWith("*")) {
                        terms.add(new SearchTerm(null, null, part.substring(1), 2));
                    } else {
                        terms.add(new SearchTerm(defaultMode, createPattern(part), "", 0));
                    }
                }
            }
            groups.add(terms);
        }
        return groups;
    }

    private boolean matchesParsedSearch(java.util.List<java.util.List<SearchTerm>> groups, T stack) {
        for (java.util.List<SearchTerm> group : groups) {
            boolean allMatch = true;
            for (SearchTerm term : group) {
                final boolean match;
                if (term.kind == 0) {
                    match = matchesSearch(term.mode, term.pattern, stack);
                } else {
                    match = matchesIdOrTag(term.text, term.kind == 1, stack);
                }
                if (!match) {
                    allMatch = false;
                    break;
                }
            }
            if (allMatch) {
                return true;
            }
        }
        return false;
    }

    private static boolean matchesIdOrTag(String text, boolean tag, IAEStack<?> stack) {
        if (stack instanceof appeng.api.storage.data.IAEItemStack) {
            final net.minecraft.item.Item item = ((appeng.api.storage.data.IAEItemStack) stack).getItem();
            if (!tag) {
                final net.minecraft.util.ResourceLocation id = item.getRegistryName();
                return id != null && id.toString().contains(text);
            }
            for (net.minecraft.util.ResourceLocation tagId : net.minecraft.tags.TagCollectionManager.getManager()
                    .getItemTags().getOwningTags(item)) {
                if (tagId.toString().contains(text)) {
                    return true;
                }
            }
            return false;
        }
        if (stack instanceof appeng.api.storage.data.IAEFluidStack && !tag) {
            final net.minecraft.util.ResourceLocation id = ((appeng.api.storage.data.IAEFluidStack) stack).getFluid()
                    .getRegistryName();
            return id != null && id.toString().contains(text);
        }
        return false;
    }

    protected abstract boolean matchesSearch(SearchMode searchMode, Pattern searchPattern, T stack);
''')
    open(path, 'w').write(s)
print('search applied')
