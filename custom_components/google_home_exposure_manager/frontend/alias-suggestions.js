/**
 * Alias suggestion generation for Google Home Exposure Manager
 * Generates natural spoken phrase variations for entity names.
 */

/**
 * Pluralize a word using common English rules.
 * @param {string} word - The word to pluralize
 * @returns {string} The pluralized word
 */
export function pluralize(word) {
  const lower = word.toLowerCase();
  if (lower.endsWith("y") && !["ay", "ey", "iy", "oy", "uy"].some(v => lower.endsWith(v))) {
    return word.slice(0, -1) + "ies";
  }
  if (lower.endsWith("s") || lower.endsWith("x") || lower.endsWith("ch") || lower.endsWith("sh")) {
    return word + "es";
  }
  if (lower.endsWith("f")) {
    return word.slice(0, -1) + "ves";
  }
  if (lower.endsWith("fe")) {
    return word.slice(0, -2) + "ves";
  }
  return word + "s";
}

/**
 * Singularize a word using common English rules.
 * @param {string} word - The word to singularize
 * @returns {string} The singularized word
 */
export function singularize(word) {
  const lower = word.toLowerCase();
  if (lower.endsWith("ies")) {
    return word.slice(0, -3) + "y";
  }
  if (lower.endsWith("ves")) {
    return word.slice(0, -3) + "f";
  }
  if (lower.endsWith("es") && (lower.endsWith("sses") || lower.endsWith("xes") || lower.endsWith("ches") || lower.endsWith("shes"))) {
    return word.slice(0, -2);
  }
  if (lower.endsWith("s") && !lower.endsWith("ss")) {
    return word.slice(0, -1);
  }
  return word;
}

/**
 * Common word synonyms - natural spoken alternatives only.
 * Maps words to arrays of alternative phrases people might say.
 */
export const WORD_SYNONYMS = {
  "light": ["lamp", "lights"],
  "lamp": ["light", "lamps"],
  "lights": ["light", "lamps"],
  "fan": ["fans", "ceiling fan"],
  "fans": ["fan", "ceiling fans"],
  "switch": ["switches"],
  "switches": ["switch"],
  "outlet": ["plug", "socket"],
  "plug": ["outlet", "socket"],
  "tv": ["television", "telly", "screen"],
  "television": ["tv", "telly"],
  "ac": ["air conditioner", "air conditioning", "cooling"],
  "air conditioner": ["ac", "cooling"],
  "heater": ["heating", "heat"],
  "heating": ["heater", "heat"],
  "thermostat": ["temperature"],
  "blind": ["blinds", "shade", "shades", "window cover"],
  "blinds": ["blind", "shades", "window covers"],
  "shade": ["shades", "blind", "blinds"],
  "shades": ["shade", "blinds"],
  "curtain": ["curtains", "drapes"],
  "curtains": ["curtain", "drapes"],
  "drape": ["drapes", "curtains"],
  "drapes": ["drape", "curtains"],
  "door": ["doors"],
  "doors": ["door"],
  "lock": ["locks", "door lock"],
  "locks": ["lock", "door locks"],
  "camera": ["cameras", "cam"],
  "cameras": ["camera", "cams"],
  "speaker": ["speakers", "music"],
  "speakers": ["speaker"],
  "vacuum": ["vacuums", "robot vacuum", "roomba"],
  "roomba": ["vacuum", "robot vacuum"],
  "garage": ["garage door"],
  "garage door": ["garage"],
};

/**
 * Natural spoken alternatives for room names.
 * Only includes phrases people would actually say to Google.
 */
export const ROOM_ALTERNATIVES = {
  "living room": ["front room", "lounge", "family room"],
  "family room": ["living room", "lounge"],
  "lounge": ["living room", "front room"],
  "bedroom": ["bed room"],
  "bed room": ["bedroom"],
  "bathroom": ["bath", "washroom", "restroom"],
  "bath": ["bathroom"],
  "master bedroom": ["main bedroom", "primary bedroom"],
  "master bathroom": ["main bathroom", "primary bathroom"],
  "kids room": ["children's room", "kid's room"],
  "guest room": ["spare room", "guest bedroom"],
  "spare room": ["guest room"],
  "dining room": ["dining area"],
  "back yard": ["backyard", "garden"],
  "backyard": ["back yard", "garden"],
  "front yard": ["front garden"],
  "patio": ["deck", "terrace"],
  "deck": ["patio", "terrace"],
  "basement": ["downstairs"],
  "upstairs": ["second floor", "upper floor"],
  "downstairs": ["first floor", "ground floor", "basement"],
};

/**
 * Generate alias suggestions for an entity based on its name.
 * @param {string} baseName - The base name of the entity
 * @param {string[]} existingAliases - Already configured aliases to exclude
 * @param {number} maxSuggestions - Maximum number of suggestions to return
 * @returns {string[]} Array of suggested aliases
 */
export function generateAliasSuggestions(baseName, existingAliases = [], maxSuggestions = 8) {
  const suggestions = new Set();
  const existingLower = new Set(existingAliases.map(a => a.toLowerCase()));
  const lowerBaseName = baseName.toLowerCase();

  // Process base name words
  const words = baseName.split(/\s+/);
  const lastWord = words[words.length - 1];
  
  // Add plural/singular variations
  const pluralLast = pluralize(lastWord);
  const singularLast = singularize(lastWord);
  
  if (pluralLast.toLowerCase() !== lastWord.toLowerCase()) {
    const pluralName = [...words.slice(0, -1), pluralLast].join(" ");
    suggestions.add(pluralName);
  }
  if (singularLast.toLowerCase() !== lastWord.toLowerCase()) {
    const singularName = [...words.slice(0, -1), singularLast].join(" ");
    suggestions.add(singularName);
  }

  // Add synonym variations
  for (const [word, syns] of Object.entries(WORD_SYNONYMS)) {
    if (lowerBaseName.includes(word)) {
      for (const syn of syns) {
        const variation = baseName.replace(new RegExp(word, "i"), syn);
        suggestions.add(variation);
      }
    }
  }

  // Add spoken alternative variations for room names
  for (const [phrase, alternatives] of Object.entries(ROOM_ALTERNATIVES)) {
    if (lowerBaseName.includes(phrase)) {
      for (const alt of alternatives) {
        const variation = baseName.replace(new RegExp(phrase, "i"), alt);
        suggestions.add(variation);
      }
    }
  }

  // Add "the" prefix variation
  if (!lowerBaseName.startsWith("the ")) {
    suggestions.add("the " + baseName);
  } else {
    suggestions.add(baseName.slice(4)); // Remove "the "
  }

  // Filter out existing aliases and the base name itself
  const filtered = [...suggestions].filter(s => 
    s.toLowerCase() !== lowerBaseName && 
    !existingLower.has(s.toLowerCase())
  );

  return filtered.slice(0, maxSuggestions);
}
