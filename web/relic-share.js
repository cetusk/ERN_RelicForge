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

/*
 * QR code transfer — a link is too long for one QR code (max ~2,900 characters), so the data is sent
 * as a stream of QR codes using a fountain code: the receiver can read ANY frames, in any order,
 * and is done after about (number of blocks + 2) useful frames, without waiting for a missed one.
 *
 *   data  = the share token's bytes, split into K blocks of SHARE_QR_BLOCK bytes (last one zero-padded)
 *   frame = "ERNRF2:<id>:<data bytes>:<K>:<seq>:<base64url of the frame's block>"
 *           seq 1..K: block seq itself; seq > K: XOR of a pseudo-random set of blocks chosen by seq
 *   The receiver solves the XOR equations (Gaussian elimination over GF(2)).
 */
const SHARE_QR_PREFIX = 'ERNRF2';
const SHARE_QR_BLOCK = 360;        // bytes per frame (~500 characters: QR version 15, easy to read)
const SHARE_QR_MAX_BLOCKS = 1000;

function shareTokenId(token) {
  let h = 0x811c9dc5;   // FNV-1a
  for (let i = 0; i < token.length; i++) {
    h ^= token.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h.toString(36);
}

/** Blocks mixed into frame `seq` (0-based block indices; the same on both sides) */
function shareQrMix(seq, blockCount) {
  if (seq <= blockCount) return [seq - 1];
  const fmix = (h) => {   // MurmurHash3 finalizer: neighbouring seq values get unrelated seeds
    h = Math.imul(h ^ (h >>> 16), 0x85ebca6b);
    h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
    return (h ^ (h >>> 16)) >>> 0;
  };
  let state = fmix(seq ^ fmix(blockCount + 0x9e3779b9));
  const random = () => {   // mulberry32
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const picked = [];
  for (let i = 0; i < blockCount; i++) if (random() < 0.5) picked.push(i);
  while (picked.length < Math.min(2, blockCount)) {
    const i = Math.floor(random() * blockCount);
    if (!picked.includes(i)) picked.push(i);
  }
  return picked.sort((a, b) => a - b);
}

/** Frame source for a share token: {blocks, frame(seq)} (seq = 1, 2, 3, ... without end) */
function createRelicShareQrSender(token) {
  const bytes = shareBase64UrlToBytes(token);
  const blockCount = Math.max(1, Math.ceil(bytes.length / SHARE_QR_BLOCK));
  const id = shareTokenId(token);
  const blocks = [];
  for (let i = 0; i < blockCount; i++) {
    const block = new Uint8Array(SHARE_QR_BLOCK);
    block.set(bytes.subarray(i * SHARE_QR_BLOCK, (i + 1) * SHARE_QR_BLOCK));
    blocks.push(block);
  }
  return {
    blocks: blockCount,
    frame(seq) {
      const out = new Uint8Array(SHARE_QR_BLOCK);
      for (const i of shareQrMix(seq, blockCount)) {
        for (let k = 0; k < SHARE_QR_BLOCK; k++) out[k] ^= blocks[i][k];
      }
      return `${SHARE_QR_PREFIX}:${id}:${bytes.length}:${blockCount}:${seq}:${shareBytesToBase64Url(out)}`;
    },
  };
}

/**
 * Rebuilds the token from scanned QR texts (a plain share link in one QR code also works).
 * add() returns {state: 'ignored' | 'progress' | 'done', received, total, token?}
 *   received = independent frames so far (the transfer is done when it reaches total)
 */
class RelicShareQrCollector {
  constructor() {
    this.reset();
  }

  reset() {
    this.key = null;
    this.total = 0;
    this.received = 0;
    this.pivots = [];   // pivots[p]: {mask, data} whose lowest set bit is p
    this.seen = new Set();
  }

  add(text) {
    const status = (state, token) => ({ state, received: this.received, total: this.total, token });
    const m = /^ERNRF2:([0-9a-z]+):(\d+):(\d+):(\d+):([A-Za-z0-9_-]+)$/.exec(String(text || '').trim());
    if (!m) {
      const linkToken = findRelicShareToken(text);
      return linkToken ? { state: 'done', received: 1, total: 1, token: linkToken } : status('ignored');
    }
    const [, id, size, count, seqText, payload] = m;
    const byteCount = Number(size);
    const blockCount = Number(count);
    const seq = Number(seqText);
    if (!(blockCount >= 1 && blockCount <= SHARE_QR_MAX_BLOCKS && seq >= 1 && byteCount >= 1)) return status('ignored');
    let data;
    try {
      data = shareBase64UrlToBytes(payload);
    } catch (_) {
      return status('ignored');
    }
    if (byteCount > blockCount * data.length || byteCount <= (blockCount - 1) * data.length) return status('ignored');
    const key = `${id}:${byteCount}:${blockCount}:${data.length}`;
    if (key !== this.key) {   // another transfer started
      this.reset();
      this.key = key;
      this.id = id;
      this.byteCount = byteCount;
      this.total = blockCount;
      this.blockSize = data.length;
    }
    if (this.seen.has(seq)) return status('progress');
    this.seen.add(seq);

    // Reduce the new equation by the known pivots; keep it if something is left
    const mask = new Uint32Array(Math.ceil(blockCount / 32));
    for (const i of shareQrMix(seq, blockCount)) mask[i >>> 5] |= 1 << (i & 31);
    for (;;) {
      const p = shareLowestBit(mask);
      if (p < 0) return status('progress');   // nothing new in this frame
      const pivot = this.pivots[p];
      if (!pivot) {
        this.pivots[p] = { mask, data };
        this.received++;
        break;
      }
      for (let w = 0; w < mask.length; w++) mask[w] ^= pivot.mask[w];
      for (let k = 0; k < data.length; k++) data[k] ^= pivot.data[k];
    }
    if (this.received < blockCount) return status('progress');

    // All blocks known: back-substitute from the last pivot
    for (let p = blockCount - 1; p >= 0; p--) {
      const row = this.pivots[p];
      for (let q = p + 1; q < blockCount; q++) {
        if (row.mask[q >>> 5] & (1 << (q & 31))) {
          const other = this.pivots[q].data;
          for (let k = 0; k < row.data.length; k++) row.data[k] ^= other[k];
        }
      }
    }
    const bytes = new Uint8Array(blockCount * this.blockSize);
    for (let p = 0; p < blockCount; p++) bytes.set(this.pivots[p].data, p * this.blockSize);
    const token = shareBytesToBase64Url(bytes.subarray(0, this.byteCount));
    if (shareTokenId(token) !== this.id) {   // should not happen (QR codes carry their own error correction)
      this.reset();
      return status('ignored');
    }
    return status('done', token);
  }
}

function shareLowestBit(mask) {
  for (let w = 0; w < mask.length; w++) {
    if (mask[w]) return w * 32 + (31 - Math.clz32(mask[w] & -mask[w]));
  }
  return -1;
}

/** Draw a QR code on a canvas (dark on white, with the standard quiet zone). Needs lib/qrcode.js. */
function drawRelicShareQr(canvas, text, maxSize) {
  const qr = qrcode(0, 'L');
  qr.addData(text, 'Byte');
  qr.make();
  const count = qr.getModuleCount();
  const quiet = 4;
  const ratio = window.devicePixelRatio || 1;
  const cell = Math.max(1, Math.floor(maxSize * ratio / (count + quiet * 2)));
  const size = cell * (count + quiet * 2);
  canvas.width = size;
  canvas.height = size;
  canvas.style.width = `${size / ratio}px`;
  canvas.style.height = `${size / ratio}px`;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, size, size);
  ctx.fillStyle = '#000';
  for (let r = 0; r < count; r++) {
    for (let c = 0; c < count; c++) {
      if (qr.isDark(r, c)) ctx.fillRect((c + quiet) * cell, (r + quiet) * cell, cell, cell);
    }
  }
}
