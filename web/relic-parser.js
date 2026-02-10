/**
 * Elden Ring Nightreign Save File Relic Parser - JavaScript Version
 * Extracts relic information from .sl2 save files in the browser.
 * Port of src/relic_parser.py
 */

// === Constants ===
const DS2_KEY_HEX = '18f6326605bd178a5524523ac0a0c609';
const IV_SIZE = 0x10;
const BND4_HEADER_LEN = 64;
const BND4_ENTRY_HEADER_LEN = 32;
const SLOT_SIZE_FULL = 80;
const SLOT_SIZE_SMALL = 16;
const EMPTY_EFFECT = 0xFFFFFFFF;

const VALID_B3_VALUES = new Set([0x80, 0x83, 0x81, 0x82, 0x84, 0x85]);
const VALID_B4_VALUES = new Set([0x80, 0x90, 0xc0]);
const SLOT_SIZE_MAP = { 0xc0: SLOT_SIZE_FULL, 0x90: SLOT_SIZE_SMALL, 0x80: SLOT_SIZE_FULL };

// Expected entry header magic bytes
const ENTRY_MAGIC = [0x40, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff];

// Character name search pattern: hex "27000046414345"
const NAME_PATTERN = [0x27, 0x00, 0x00, 0x46, 0x41, 0x43, 0x45];

// === Helper Functions ===

/**
 * Read a little-endian 24-bit unsigned integer from Uint8Array
 */
function readUint24LE(data, offset) {
  return data[offset] | (data[offset + 1] << 8) | (data[offset + 2] << 16);
}

/**
 * Read a little-endian 32-bit unsigned integer from Uint8Array
 */
function readUint32LE(data, offset) {
  return (data[offset] | (data[offset + 1] << 8) |
          (data[offset + 2] << 16) | (data[offset + 3] << 24)) >>> 0;
}

/**
 * Read a little-endian 16-bit unsigned integer from Uint8Array
 */
function readUint16LE(data, offset) {
  return data[offset] | (data[offset + 1] << 8);
}

/**
 * Check if data starts with the given pattern at the given offset
 */
function startsWithAt(data, pattern, offset) {
  if (offset + pattern.length > data.length) return false;
  for (let i = 0; i < pattern.length; i++) {
    if (data[offset + i] !== pattern[i]) return false;
  }
  return true;
}

/**
 * Find a byte pattern in data starting from offset
 * Returns the position or -1 if not found
 */
function findPattern(data, pattern, startOffset) {
  const len = data.length;
  const patLen = pattern.length;
  const searchEnd = len - patLen;
  for (let i = startOffset; i <= searchEnd; i++) {
    let match = true;
    for (let j = 0; j < patLen; j++) {
      if (data[i + j] !== pattern[j]) {
        match = false;
        break;
      }
    }
    if (match) return i;
  }
  return -1;
}

/**
 * Convert Uint8Array to hex string
 */
function bytesToHex(bytes) {
  let hex = '';
  for (let i = 0; i < bytes.length; i++) {
    hex += bytes[i].toString(16).padStart(2, '0');
  }
  return hex;
}

/**
 * Convert hex string to byte array
 */
function hexToBytes(hex) {
  const bytes = [];
  for (let i = 0; i < hex.length; i += 2) {
    bytes.push(parseInt(hex.substring(i, i + 2), 16));
  }
  return bytes;
}

// === AES-CBC Decryption ===

/**
 * Decrypt AES-CBC encrypted data
 * @param {Uint8Array} iv - 16-byte initialization vector
 * @param {Uint8Array} encryptedPayload - encrypted data
 * @returns {Uint8Array} decrypted data
 */
function decryptAES(iv, encryptedPayload) {
  const key = CryptoJS.enc.Hex.parse(DS2_KEY_HEX);
  const ivWords = CryptoJS.lib.WordArray.create(iv);
  const ciphertext = CryptoJS.lib.WordArray.create(encryptedPayload);

  const decrypted = CryptoJS.AES.decrypt(
    { ciphertext: ciphertext },
    key,
    {
      iv: ivWords,
      mode: CryptoJS.mode.CBC,
      padding: CryptoJS.pad.NoPadding,
    }
  );

  // Convert WordArray to Uint8Array
  const words = decrypted.words;
  const sigBytes = decrypted.sigBytes;
  const result = new Uint8Array(sigBytes);
  for (let i = 0; i < sigBytes; i++) {
    result[i] = (words[i >>> 2] >>> (24 - (i % 4) * 8)) & 0xff;
  }
  return result;
}

// === BND4 Entry Processing ===

/**
 * Decrypt a BND4 save file
 * @param {ArrayBuffer} arrayBuffer - raw file data
 * @returns {Array} array of BND4 entry objects with clean_data
 */
function decryptSaveFile(arrayBuffer) {
  const raw = new Uint8Array(arrayBuffer);

  // Check BND4 header
  if (!startsWithAt(raw, [0x42, 0x4E, 0x44, 0x34], 0)) { // "BND4"
    throw new Error("BND4 header not found! This doesn't appear to be a valid SL2 file.");
  }

  const numEntries = readUint32LE(raw, 12);
  const entries = [];

  for (let i = 0; i < numEntries; i++) {
    const pos = BND4_HEADER_LEN + BND4_ENTRY_HEADER_LEN * i;

    if (pos + BND4_ENTRY_HEADER_LEN > raw.length) {
      console.warn(`File too small to read entry #${i} header`);
      break;
    }

    // Check entry header magic
    if (!startsWithAt(raw, ENTRY_MAGIC, pos)) {
      console.warn(`Entry header #${i} does not match expected magic - skipping`);
      continue;
    }

    const entrySize = readUint32LE(raw, pos + 8);
    const entryDataOffset = readUint32LE(raw, pos + 16);

    // Validity checks
    if (entrySize <= 0 || entrySize > 1000000000) {
      console.warn(`Entry #${i} has invalid size: ${entrySize} - skipping`);
      continue;
    }

    if (entryDataOffset <= 0 || entryDataOffset >= raw.length ||
        entryDataOffset + entrySize > raw.length) {
      console.warn(`Entry #${i} has invalid data offset: ${entryDataOffset} - skipping`);
      continue;
    }

    try {
      const encryptedData = raw.slice(entryDataOffset, entryDataOffset + entrySize);
      const iv = encryptedData.slice(0, IV_SIZE);
      const encryptedPayload = encryptedData.slice(IV_SIZE);

      const decryptedRaw = decryptAES(iv, encryptedPayload);
      // Skip first 4 bytes of decrypted data
      const cleanData = decryptedRaw.slice(4);

      entries.push({
        index: i,
        name: `USERDATA_${String(i).padStart(2, '0')}`,
        cleanData: cleanData,
      });
    } catch (e) {
      console.warn(`Error processing entry #${i}:`, e);
      continue;
    }
  }

  return entries;
}

// === Character Name Extraction ===

/**
 * Extract character name from BND4 entries
 * @param {Array} entries - BND4 entries
 * @returns {string} character name
 */
function getCharacterName(entries) {
  for (const entry of entries) {
    const data = entry.cleanData;
    const patternPos = findPattern(data, NAME_PATTERN, 0);

    if (patternPos !== -1) {
      const nameOffset = patternPos - 51;
      if (nameOffset < 0) continue;

      // Find proper UTF-16LE null terminator
      const searchEnd = Math.min(nameOffset + 200, data.length - 1);
      for (let i = nameOffset; i < searchEnd; i++) {
        if (data[i] === 0 && data[i + 1] === 0) {
          // Check alignment
          if ((i - nameOffset) % 2 === 0) {
            const nameBytes = data.slice(nameOffset, i);
            try {
              const decoder = new TextDecoder('utf-16le');
              return decoder.decode(nameBytes);
            } catch (e) {
              return 'Unknown';
            }
          }
        }
      }
    }
  }

  return 'Unknown';
}

// === Relic Parsing ===

/**
 * Parse relics from a decrypted entry
 * @param {Uint8Array} entryData - decrypted entry data
 * @param {Set} validItems - set of valid item IDs
 * @param {Set} validEffects - set of valid effect IDs
 * @returns {Array} array of relic objects
 */
function parseRelicsFromEntry(entryData, validItems, validEffects) {
  const dataLength = entryData.length;
  const potentialSlots = [];
  const searchLimit = dataLength - 4;

  // First pass: find potential relic slots
  for (let pos = 0; pos < searchLimit; pos++) {
    const b3 = entryData[pos + 2];
    const b4 = entryData[pos + 3];

    if (VALID_B3_VALUES.has(b3) && VALID_B4_VALUES.has(b4)) {
      const slotSize = SLOT_SIZE_MAP[b4];
      if (!slotSize || pos + slotSize > dataLength) continue;

      // Extract IDs
      const relicId = readUint32LE(entryData, pos);
      const itemId = readUint24LE(entryData, pos + 4);

      // Validate item ID
      if (!validItems.has(itemId)) continue;

      // Extract effect IDs
      const effectKeys = [
        readUint32LE(entryData, pos + 16),
        readUint32LE(entryData, pos + 20),
        readUint32LE(entryData, pos + 24),
        readUint32LE(entryData, pos + 28),
      ];

      // Validate effects
      let allValid = true;
      let validCount = 0;
      for (const effId of effectKeys) {
        if (effId !== EMPTY_EFFECT) {
          if (!validEffects.has(effId)) {
            allValid = false;
            break;
          }
          validCount++;
        }
      }

      if (!allValid || validCount === 0) continue;

      // Extract debuff keys
      const debuffKeys = [
        readUint32LE(entryData, pos + 56),
        readUint32LE(entryData, pos + 60),
        readUint32LE(entryData, pos + 64),
        readUint32LE(entryData, pos + 68),
      ];

      // Build effects list
      const effects = [];
      for (let idx = 0; idx < effectKeys.length; idx++) {
        const effKey = effectKeys[idx];
        if (effKey !== EMPTY_EFFECT) {
          const debuffKey = debuffKeys[idx];
          if (debuffKey !== EMPTY_EFFECT) {
            effects.push([effKey, debuffKey]);
          } else {
            effects.push([effKey]);
          }
        }
      }

      // Store potential slot
      const idBytes = entryData.slice(pos, pos + 4);
      potentialSlots.push({
        id: relicId,
        idBytes: idBytes,
        itemId: itemId,
        effects: effects,
      });
    }
  }

  // Second pass: find sort keys
  const relics = [];
  for (const slot of potentialSlots) {
    const hexPattern = hexToBytes(bytesToHex(slot.idBytes) + '01000000');
    const sortKeyOffset = findPattern(entryData, hexPattern, 0);

    if (sortKeyOffset !== -1) {
      const sortKey = readUint16LE(entryData, sortKeyOffset + 8);
      relics.push({
        id: slot.id,
        itemId: slot.itemId,
        effects: slot.effects,
        sortKey: sortKey,
      });
    }
  }

  // Sort by sort key (descending)
  relics.sort((a, b) => b.sortKey - a.sortKey);
  return relics;
}

// === Coordinate Assignment ===

/**
 * Set coordinates for relics
 * @param {Array} relics - parsed relics
 * @param {Object} itemsData - items data (id -> info)
 * @returns {Array} relics with coordinates set
 */
function setCoordinates(relics, itemsData) {
  function isDeepRelic(itemId) {
    const item = itemsData[itemId];
    return item && item.type === 'DeepRelic';
  }

  function getColor(itemId) {
    const item = itemsData[itemId];
    return item ? item.color || 'Red' : 'Red';
  }

  // Separate normal and deep relics
  const normalRelics = [];
  const deepRelics = [];
  for (const relic of relics) {
    if (isDeepRelic(relic.itemId)) {
      deepRelics.push(relic);
    } else {
      normalRelics.push(relic);
    }
  }

  const colors = ['Red', 'Blue', 'Yellow', 'Green'];

  // Group by color
  const relicsByColor = {};
  const deepRelicsByColor = {};
  for (const color of colors) {
    relicsByColor[color] = normalRelics.filter(r => getColor(r.itemId) === color);
    deepRelicsByColor[color] = deepRelics.filter(r => getColor(r.itemId) === color);
  }

  // Set coordinates for normal relics (8 per row)
  for (let i = 0; i < normalRelics.length; i++) {
    const relic = normalRelics[i];
    relic.coordinates = [i >> 3, i & 7];
    const color = getColor(relic.itemId);
    const colorIndex = relicsByColor[color].indexOf(relic);
    relic.coordinatesByColor = [colorIndex >> 3, colorIndex & 7];
  }

  // Set coordinates for deep relics (8 per row)
  for (let i = 0; i < deepRelics.length; i++) {
    const relic = deepRelics[i];
    relic.coordinates = [i >> 3, i & 7];
    const color = getColor(relic.itemId);
    const colorIndex = deepRelicsByColor[color].indexOf(relic);
    relic.coordinatesByColor = [colorIndex >> 3, colorIndex & 7];
  }

  return relics;
}

// === Main Parse Function ===

/**
 * Parse an SL2 save file and return structured relic data
 * @param {ArrayBuffer} arrayBuffer - raw file data
 * @param {Object} itemsData - items data { items: { id: { key, color, type, ... } } }
 * @param {Object} effectsData - effects data { effects: { id: { key, name_en, name_ja, ... } } }
 * @returns {Object} parsed relic data
 */
function parseSaveFile(arrayBuffer, itemsData, effectsData) {
  // Build lookup maps
  const itemsMap = {};
  for (const [id, item] of Object.entries(itemsData.items || {})) {
    itemsMap[parseInt(id)] = item;
  }

  const effectsMap = {};
  for (const [id, effect] of Object.entries(effectsData.effects || {})) {
    effectsMap[parseInt(id)] = effect;
  }

  const validItems = new Set(Object.keys(itemsMap).map(Number));
  const validEffects = new Set(Object.keys(effectsMap).map(Number));

  // Decrypt save file
  const entries = decryptSaveFile(arrayBuffer);
  if (entries.length === 0) {
    throw new Error('No BND4 entries found');
  }

  // Get character name
  const characterName = getCharacterName(entries);

  // Parse relics from Entry 0 only
  const entry0 = entries[0];
  const relics = parseRelicsFromEntry(entry0.cleanData, validItems, validEffects);

  // Set coordinates
  setCoordinates(relics, itemsMap);

  // Convert to output format
  const relicsOutput = [];
  for (const relic of relics) {
    const effectsList = [];
    for (const effectGroup of relic.effects) {
      const effectDict = [];
      for (const effId of effectGroup) {
        const effInfo = effectsMap[effId] || {};
        const effNameEn = effInfo.name_en || effInfo.key || `Unknown Effect ${effId}`;
        const effNameJa = effInfo.name_ja || effNameEn;
        const effKey = effInfo.key || String(effId);

        effectDict.push({
          id: effId,
          key: effKey,
          name_en: effNameEn,
          name_ja: effNameJa,
        });
      }
      effectsList.push(effectDict);
    }

    const itemInfo = itemsMap[relic.itemId] || {};
    const itemKey = itemInfo.key || `Unknown Item ${relic.itemId}`;
    const itemNameEn = itemInfo.name_en || itemKey;
    const itemNameJa = itemInfo.name_ja || itemNameEn;

    relicsOutput.push({
      id: relic.id,
      itemId: relic.itemId,
      itemKey: itemKey,
      itemNameEn: itemNameEn,
      itemNameJa: itemNameJa,
      itemColor: itemInfo.color || null,
      itemType: itemInfo.type || null,
      effects: effectsList,
      coordinates: relic.coordinates,
      coordinatesByColor: relic.coordinatesByColor,
      sortKey: relic.sortKey || 0,
    });
  }

  return {
    file: 'uploaded',
    characterName: characterName,
    totalRelics: relicsOutput.length,
    relics: relicsOutput,
  };
}
