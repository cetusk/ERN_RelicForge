/**
 * Share links — pack the relics shown in the app into a URL fragment ("#r=...")
 * so they can be opened on another device (e.g. a phone) without the save file.
 *
 * The fragment is never sent to the web server. Relic IDs and sort keys are not
 * included (order is kept, IDs are renumbered), which keeps links short.
 *
 * Format v1 (then deflate-raw + base64url):
 *   'R' 0x01 | flags (bit0: character name present)
 *   [varint len + UTF-8 name]
 *   varint nEffects, effect IDs (ascending, delta varints)
 *   varint nItems,   item IDs   (ascending, delta varints)
 *   varint nRelics
 *   bit stream per relic (in display order):
 *     item index (itemBits) | effect count (3 bits) |
 *     per effect: has-debuff (1 bit) | effect index (effectBits) [| debuff index (effectBits)]
 */

const SHARE_PARAM = 'r';
const SHARE_PUBLIC_URL = 'https://cetusk.github.io/ERN_RelicForge/web/index.html';
const SHARE_FORMAT_VERSION = 1;
const SHARE_MAX_RELICS = 20000;

function shareBitsFor(count) {
  return Math.max(1, Math.ceil(Math.log2(Math.max(count, 2))));
}

function shareBytesToBase64Url(bytes) {
  let bin = '';
  for (let i = 0; i < bytes.length; i += 0x8000) {
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  }
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function shareBase64UrlToBytes(text) {
  const b64 = text.replace(/-/g, '+').replace(/_/g, '/');
  const bin = atob(b64 + '='.repeat((4 - b64.length % 4) % 4));
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

async function shareTransform(bytes, Stream) {
  if (typeof Stream === 'undefined') {
    throw new Error('This browser does not support compression streams');
  }
  const stream = new Blob([bytes]).stream().pipeThrough(new Stream('deflate-raw'));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

/**
 * Encode relics into a share token.
 * @param {{characterName: string, relics: Array}} data - relics in compact form [id, itemId, sortKey, effects]
 * @param {{includeName?: boolean}} options
 * @returns {Promise<string>} base64url token (put after "#r=")
 */
async function encodeRelicShare(data, options = {}) {
  const includeName = options.includeName !== false && !!data.characterName;
  const relics = [...data.relics].sort((a, b) => b[2] - a[2]);   // display order (sort key desc)
  const effectIds = [...new Set(relics.flatMap(r => r[3].flat()))].sort((a, b) => a - b);
  const itemIds = [...new Set(relics.map(r => r[1]))].sort((a, b) => a - b);
  const effectIndex = new Map(effectIds.map((v, i) => [v, i]));
  const itemIndex = new Map(itemIds.map((v, i) => [v, i]));
  const effectBits = shareBitsFor(effectIds.length);
  const itemBits = shareBitsFor(itemIds.length);

  const out = [];
  const varint = (n) => {
    do {
      let b = n & 0x7f;
      n = Math.floor(n / 128);
      if (n) b |= 0x80;
      out.push(b);
    } while (n);
  };
  out.push(0x52, SHARE_FORMAT_VERSION, includeName ? 1 : 0);
  if (includeName) {
    const name = new TextEncoder().encode(data.characterName);
    varint(name.length);
    out.push(...name);
  }
  for (const ids of [effectIds, itemIds]) {
    varint(ids.length);
    let prev = 0;
    for (const v of ids) { varint(v - prev); prev = v; }
  }
  varint(relics.length);

  let acc = 0, accBits = 0;
  const put = (value, width) => {
    for (let i = 0; i < width; i++) {
      acc |= ((value >>> i) & 1) << accBits;
      if (++accBits === 8) { out.push(acc); acc = 0; accBits = 0; }
    }
  };
  for (const [, itemId, , effects] of relics) {
    put(itemIndex.get(itemId), itemBits);
    put(effects.length, 3);
    for (const group of effects) {
      put(group.length > 1 ? 1 : 0, 1);
      put(effectIndex.get(group[0]), effectBits);
      if (group.length > 1) put(effectIndex.get(group[1]), effectBits);
    }
  }
  if (accBits) out.push(acc);

  const packed = await shareTransform(new Uint8Array(out), typeof CompressionStream !== 'undefined' ? CompressionStream : undefined);
  return shareBytesToBase64Url(packed);
}

/**
 * Decode a share token (validates everything; throws on malformed input).
 * @returns {Promise<{characterName: string, relics: Array}>} relics in compact form
 */
async function decodeRelicShare(token) {
  const bytes = await shareTransform(shareBase64UrlToBytes(token),
    typeof DecompressionStream !== 'undefined' ? DecompressionStream : undefined);
  let pos = 0;
  const fail = (why) => { throw new Error(`Invalid share data (${why})`); };
  const byte = () => (pos < bytes.length ? bytes[pos++] : fail('truncated'));
  const varint = () => {
    let n = 0, mul = 1, b;
    do {
      b = byte();
      n += (b & 0x7f) * mul;
      mul *= 128;
      if (mul > 2 ** 35) fail('varint');
    } while (b & 0x80);
    return n;
  };
  if (byte() !== 0x52) fail('magic');
  if (byte() !== SHARE_FORMAT_VERSION) fail('version');
  const flags = byte();
  let characterName = '';
  if (flags & 1) {
    const len = varint();
    if (len > 256 || pos + len > bytes.length) fail('name');
    characterName = new TextDecoder().decode(bytes.subarray(pos, pos + len));
    pos += len;
  }
  const readIds = () => {
    const count = varint();
    if (count > 100000) fail('table size');
    const ids = [];
    let prev = 0;
    for (let i = 0; i < count; i++) {
      prev += varint();
      if (prev >= 0x01000000) fail('id');
      ids.push(prev);
    }
    return ids;
  };
  const effectIds = readIds();
  const itemIds = readIds();
  const relicCount = varint();
  if (relicCount > SHARE_MAX_RELICS) fail('relic count');
  const effectBits = shareBitsFor(effectIds.length);
  const itemBits = shareBitsFor(itemIds.length);

  let acc = 0, accBits = 0;
  const get = (width) => {
    let v = 0;
    for (let i = 0; i < width; i++) {
      if (accBits === 0) { acc = byte(); accBits = 8; }
      v |= (acc & 1) << i;
      acc >>= 1;
      accBits--;
    }
    return v >>> 0;
  };
  const pick = (table, index) => (index < table.length ? table[index] : fail('index'));
  const relics = [];
  for (let i = 0; i < relicCount; i++) {
    const itemId = pick(itemIds, get(itemBits));
    const effectCount = get(3);
    if (effectCount > 4) fail('effect count');
    const effects = [];
    for (let e = 0; e < effectCount; e++) {
      const hasDebuff = get(1);
      const group = [pick(effectIds, get(effectBits))];
      if (hasDebuff) group.push(pick(effectIds, get(effectBits)));
      effects.push(group);
    }
    // IDs / sort keys are not shared: renumber, keeping the display order
    relics.push([i + 1, itemId, relicCount - i, effects]);
  }
  return { characterName, relics };
}

/** Full share URL for a token (base: page URL without hash / query) */
function relicShareUrl(base, token) {
  return `${base}#${SHARE_PARAM}=${token}`;
}

/** Find a share token in a URL, a URL fragment or pasted / file text */
function findRelicShareToken(text) {
  const m = String(text || '').match(new RegExp(`[#?&]${SHARE_PARAM}=([A-Za-z0-9_-]+)`));
  return m ? m[1] : null;
}
