#!/usr/bin/env python3
"""
Elden Ring Nightreign Save File Relic Parser - Optimized Version
Extracts relic information from .sl2 save files and outputs to JSON
"""

import json
import struct
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from Crypto.Cipher import AES
import sys

# Decryption key for Elden Ring Nightreign
DS2_KEY = bytes([
    0x18, 0xf6, 0x32, 0x66, 0x05, 0xbd, 0x17, 0x8a,
    0x55, 0x24, 0x52, 0x3a, 0xc0, 0xa0, 0xc6, 0x09
])

# Constants
IV_SIZE = 0x10
BND4_HEADER_LEN = 64
BND4_ENTRY_HEADER_LEN = 32

# Relic slot constants
SLOT_SIZE_FULL = 80
SLOT_SIZE_SMALL = 16
EMPTY_EFFECT = 0xFFFFFFFF

# Valid byte patterns
VALID_B3_VALUES = frozenset({0x80, 0x83, 0x81, 0x82, 0x84, 0x85})
VALID_B4_VALUES = frozenset({0x80, 0x90, 0xc0})

# Slot size mapping (using dict for O(1) lookup)
SLOT_SIZE_MAP = {
    0xc0: SLOT_SIZE_FULL,
    0x90: SLOT_SIZE_SMALL,
    0x80: SLOT_SIZE_FULL,
}


@dataclass
class BND4Entry:
    """Represents a decrypted BND4 entry"""
    index: int
    name: str
    clean_data: bytes


class SaveFileDecryptor:
    """Handles decryption of Elden Ring Nightreign save files"""
    
    @staticmethod
    def read_int32_le(data: bytes, offset: int) -> int:
        """Read a little-endian 32-bit integer"""
        return struct.unpack_from('<I', data, offset)[0]
    
    @staticmethod
    def array_starts_with(data: bytes, pattern: bytes) -> bool:
        """Check if array starts with pattern"""
        return len(data) >= len(pattern) and data[:len(pattern)] == pattern
    
    @staticmethod
    def decrypt_aes(key: bytes, iv: bytes, data: bytes) -> bytes:
        """Decrypt AES-CBC encrypted data"""
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return cipher.decrypt(data)

    @staticmethod
    def _create_aes_decryptor(key: bytes):
        """Create a reusable AES decryptor factory for the given key.
        Returns a function that takes (iv, data) and returns decrypted data.
        pycryptodome requires a new cipher per IV, but caching the key
        avoids repeated parameter validation overhead."""
        def decrypt(iv: bytes, data: bytes) -> bytes:
            return AES.new(key, AES.MODE_CBC, iv).decrypt(data)
        return decrypt

    @staticmethod
    def decrypt_save_file(file_path: str) -> List[BND4Entry]:
        """Main function to decrypt SL2 save file"""
        with open(file_path, 'rb') as f:
            raw = f.read()
        
        # Check BND4 header
        if not SaveFileDecryptor.array_starts_with(raw, b'BND4'):
            raise ValueError("BND4 header not found! This doesn't appear to be a valid SL2 file.")
        
        num_bnd4_entries = SaveFileDecryptor.read_int32_le(raw, 12)
        bnd4_entries = []

        # Expected entry header magic
        expected_magic = b'\x40\x00\x00\x00\xff\xff\xff\xff'

        # Create cached AES decryptor for the key
        aes_decrypt = SaveFileDecryptor._create_aes_decryptor(DS2_KEY)

        # Process all BND4 entries
        for i in range(num_bnd4_entries):
            pos = BND4_HEADER_LEN + BND4_ENTRY_HEADER_LEN * i
            
            if pos + BND4_ENTRY_HEADER_LEN > len(raw):
                print(f"Warning: File too small to read entry #{i} header", file=sys.stderr)
                break
            
            entry_header = raw[pos:pos + BND4_ENTRY_HEADER_LEN]
            
            # Check entry header magic
            if not SaveFileDecryptor.array_starts_with(entry_header, expected_magic):
                print(f"Warning: Entry header #{i} does not match expected magic - skipping", file=sys.stderr)
                continue
            
            entry_size = SaveFileDecryptor.read_int32_le(entry_header, 8)
            entry_data_offset = SaveFileDecryptor.read_int32_le(entry_header, 16)
            
            # Validity checks
            if not (0 < entry_size <= 1000000000):
                print(f"Warning: Entry #{i} has invalid size: {entry_size} - skipping", file=sys.stderr)
                continue
            
            if not (0 < entry_data_offset < len(raw) and entry_data_offset + entry_size <= len(raw)):
                print(f"Warning: Entry #{i} has invalid data offset: {entry_data_offset} - skipping", file=sys.stderr)
                continue
            
            try:
                iv = raw[entry_data_offset:entry_data_offset + IV_SIZE]
                encrypted_payload = raw[entry_data_offset + IV_SIZE:entry_data_offset + entry_size]

                decrypted_raw = aes_decrypt(iv, encrypted_payload)
                clean_data = decrypted_raw[4:]

                entry = BND4Entry(
                    index=i,
                    name=f'USERDATA_{i:02d}',
                    clean_data=clean_data
                )
                bnd4_entries.append(entry)
            except Exception as e:
                print(f"Error processing entry #{i}: {e}", file=sys.stderr)
                continue
        
        return bnd4_entries


class RelicParser:
    """Parses relic information from decrypted save data"""
    
    # Character name pattern
    NAME_PATTERN = bytes.fromhex("27000046414345")
    
    @staticmethod
    def find_hex_offset(data: bytes, hex_pattern: str, offset: int = 0) -> Optional[int]:
        """Find the offset of a hex pattern in data"""
        try:
            pattern_bytes = bytes.fromhex(hex_pattern.replace(' ', '').lower())
            pos = data.find(pattern_bytes, max(0, min(offset, len(data))))
            return pos if pos != -1 else None
        except Exception:
            return None
    
    @staticmethod
    def read_int_le(data: bytes) -> int:
        """Read a little-endian integer from bytes (optimized)"""
        result = 0
        for i, byte in enumerate(data):
            result |= byte << (i << 3)  # Bit shift instead of multiplication
        return result
    
    @staticmethod
    def get_character_name(bnd4_entries: List[BND4Entry]) -> str:
        """Extract character name from BND4 entries"""
        for entry in bnd4_entries:
            pattern_offset = entry.clean_data.find(RelicParser.NAME_PATTERN)
            
            if pattern_offset != -1:
                name_offset = pattern_offset - 51
                if name_offset < 0 or name_offset >= len(entry.clean_data):
                    continue

                # Find proper UTF-16LE null terminator
                for i in range(name_offset, min(name_offset + 200, len(entry.clean_data) - 1)):
                    if entry.clean_data[i] == 0 and entry.clean_data[i + 1] == 0:
                        # Check alignment
                        if (i - name_offset) % 2 == 0:
                            name_bytes = entry.clean_data[name_offset:i]
                            try:
                                return name_bytes.decode('utf-16-le')
                            except UnicodeDecodeError:
                                return "Unknown"
        
        return "Unknown"
    
    @staticmethod
    def get_slot_size(b4: int) -> Optional[int]:
        """Get slot size based on b4 byte value (O(1) dict lookup)"""
        return SLOT_SIZE_MAP.get(b4)
    
    @staticmethod
    def parse_relics_from_entry(
        entry_data: bytes,
        valid_items: Set[int],
        valid_effects: Set[int]
    ) -> List[Dict]:
        """Parse relics with validation from entry data (optimized)"""
        data_length = len(entry_data)
        potential_slots = []
        unpack = struct.unpack_from

        # Pre-compute commonly used values
        search_limit = data_length - 4

        # First pass: find potential relic slots
        pos = 0
        while pos < search_limit:
            b3 = entry_data[pos + 2]
            b4 = entry_data[pos + 3]

            if b3 in VALID_B3_VALUES and b4 in VALID_B4_VALUES:
                slot_size = SLOT_SIZE_MAP.get(b4)

                if slot_size and pos + slot_size <= data_length:
                    # Extract IDs directly from entry_data (no slice)
                    relic_id = unpack('<I', entry_data, pos)[0]
                    item_id = int.from_bytes(entry_data[pos + 4:pos + 7], 'little')

                    # Validate item ID (early exit if invalid)
                    if item_id not in valid_items:
                        pos += 1
                        continue

                    # Extract 4 effect IDs in one unpack call
                    effect_keys = unpack('<IIII', entry_data, pos + 16)

                    # Validate effects (early exit on first invalid)
                    valid_count = 0
                    all_valid = True
                    for eff_id in effect_keys:
                        if eff_id != EMPTY_EFFECT:
                            if eff_id not in valid_effects:
                                all_valid = False
                                break
                            valid_count += 1

                    if not all_valid or valid_count == 0:
                        pos += 1
                        continue

                    # Extract 4 debuff keys in one unpack call
                    debuff_keys = unpack('<IIII', entry_data, pos + 56)

                    # Build effects list
                    effects = []
                    for idx, eff_key in enumerate(effect_keys):
                        if eff_key != EMPTY_EFFECT:
                            debuff_key = debuff_keys[idx]
                            if debuff_key != EMPTY_EFFECT:
                                effects.append([eff_key, debuff_key])
                            else:
                                effects.append([eff_key])

                    # Store potential slot
                    potential_slots.append({
                        'id': relic_id,
                        'item_id': item_id,
                        'effects': effects,
                    })

            pos += 1

        # Build sort key index using C-level find (O(N) amortized)
        sort_key_index = {}
        marker = b'\x01\x00\x00\x00'
        search_pos = 4
        while True:
            search_pos = entry_data.find(marker, search_pos)
            if search_pos == -1:
                break
            candidate_id = unpack('<I', entry_data, search_pos - 4)[0]
            if candidate_id not in sort_key_index:
                sort_key_index[candidate_id] = search_pos - 4
            search_pos += 1

        # Second pass: look up sort keys from index (O(1) per relic)
        relics = []
        for slot in potential_slots:
            sort_key_pos = sort_key_index.get(slot['id'])
            if sort_key_pos is not None:
                sort_key = unpack('<H', entry_data, sort_key_pos + 8)[0]
                relics.append({
                    'id': slot['id'],
                    'item_id': slot['item_id'],
                    'effects': slot['effects'],
                    'sort_key': sort_key
                })

        # Sort by sort key (descending)
        relics.sort(key=lambda x: x['sort_key'], reverse=True)
        return relics
    
    @staticmethod
    def set_coordinates(relics: List[Dict], items_data: Dict) -> List[Dict]:
        """Set coordinates for relics (optimized single-pass)"""
        normal_color_counters = {'Red': 0, 'Blue': 0, 'Yellow': 0, 'Green': 0}
        deep_color_counters = {'Red': 0, 'Blue': 0, 'Yellow': 0, 'Green': 0}
        normal_idx = 0
        deep_idx = 0

        for relic in relics:
            item = items_data.get(relic['item_id'], {})
            color = item.get('color', 'Red')
            is_deep = item.get('type') == 'DeepRelic'

            if is_deep:
                relic['coordinates'] = [deep_idx >> 3, deep_idx & 7]
                color_idx = deep_color_counters[color]
                relic['coordinates_by_color'] = [color_idx >> 3, color_idx & 7]
                deep_color_counters[color] += 1
                deep_idx += 1
            else:
                relic['coordinates'] = [normal_idx >> 3, normal_idx & 7]
                color_idx = normal_color_counters[color]
                relic['coordinates_by_color'] = [color_idx >> 3, color_idx & 7]
                normal_color_counters[color] += 1
                normal_idx += 1

        return relics


def load_items_data(items_file: str) -> Dict[int, Dict]:
    """Load items data from JSON"""
    try:
        with open(items_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        items_dict = {int(k): v for k, v in data.get('items', {}).items()}
        print(f"Loaded {len(items_dict)} items from {items_file}", file=sys.stderr)
        return items_dict
    except Exception as e:
        print(f"Error loading items data: {e}", file=sys.stderr)
        return {}


def load_effects_data(effects_file: str) -> Dict[int, Dict]:
    """Load effects data from JSON"""
    try:
        with open(effects_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        effects_dict = {int(k): v for k, v in data.get('effects', {}).items()}
        print(f"Loaded {len(effects_dict)} effects from {effects_file}", file=sys.stderr)
        return effects_dict
    except Exception as e:
        print(f"Error loading effects data: {e}", file=sys.stderr)
        return {}


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract relic information from Elden Ring Nightreign save files')
    parser.add_argument('input_file', help='Input .sl2 save file')
    parser.add_argument('-o', '--output', help='Output JSON file (default: output.json)', default='output.json')
    parser.add_argument('--items', help='Items data JSON file', default='resources/items_data.json')
    parser.add_argument('--effects', help='Effects data JSON file', default='resources/effects_data.json')
    
    args = parser.parse_args()
    
    # Load data files
    items_data = load_items_data(args.items)
    effects_data = load_effects_data(args.effects)
    
    if not items_data or not effects_data:
        print("Error: Could not load items or effects data", file=sys.stderr)
        sys.exit(1)
    
    # Convert to sets for O(1) lookup
    valid_items = set(items_data.keys())
    valid_effects = set(effects_data.keys())
    
    try:
        # Decrypt save file
        print(f"Decrypting save file: {args.input_file}")
        bnd4_entries = SaveFileDecryptor.decrypt_save_file(args.input_file)
        print(f"Found {len(bnd4_entries)} BND4 entries")
        
        # Get character name
        character_name = RelicParser.get_character_name(bnd4_entries)
        print(f"Character name: {character_name}")
        
        # Parse relics from Entry 0 only (Entry 13 is a mirror)
        if not bnd4_entries:
            raise ValueError("No BND4 entries found")
        
        entry0 = bnd4_entries[0]
        print(f"\nParsing relics from Entry 0...")
        
        relics = RelicParser.parse_relics_from_entry(
            entry0.clean_data,
            valid_items,
            valid_effects
        )
        
        print(f"Found {len(relics)} active relics")
        
        # Set coordinates
        relics = RelicParser.set_coordinates(relics, items_data)
        
        # Convert to output format
        relics_output = []
        for relic in relics:
            effects_list = []
            for effect_group in relic['effects']:
                effect_dict = []
                for eff_id in effect_group:
                    eff_info = effects_data.get(eff_id, {})
                    if isinstance(eff_info, dict):
                        eff_name_en = eff_info.get('name_en', eff_info.get('key', f"Unknown Effect {eff_id}"))
                        eff_name_ja = eff_info.get('name_ja', eff_name_en)
                        eff_key = eff_info.get('key', eff_id)
                    else:
                        eff_name_en = eff_info if eff_info else f"Unknown Effect {eff_id}"
                        eff_name_ja = eff_name_en
                        eff_key = eff_id

                    effect_dict.append({
                        'id': eff_id,
                        'key': eff_key,
                        'name_en': eff_name_en,
                        'name_ja': eff_name_ja
                    })
                effects_list.append(effect_dict)
            
            item_info = items_data.get(relic['item_id'], {})
            item_key = item_info.get('key', f"Unknown Item {relic['item_id']}")
            item_name_en = item_info.get('name_en', item_key)
            item_name_ja = item_info.get('name_ja', item_name_en)

            relics_output.append({
                'id': relic['id'],
                'itemId': relic['item_id'],
                'itemKey': item_key,
                'itemNameEn': item_name_en,
                'itemNameJa': item_name_ja,
                'itemColor': item_info.get('color'),
                'itemType': item_info.get('type'),
                'effects': effects_list,
                'coordinates': relic['coordinates'],
                'coordinatesByColor': relic['coordinates_by_color'],
                'sortKey': relic.get('sort_key', 0)
            })
        
        # Output JSON
        output_data = {
            'file': args.input_file,
            'characterName': character_name,
            'totalRelics': len(relics_output),
            'relics': relics_output
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSuccessfully extracted relic data to: {args.output}")
        print(f"Total relics: {len(relics_output)}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()