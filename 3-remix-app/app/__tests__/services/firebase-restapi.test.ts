import { describe, it, expect } from '@jest/globals';
import { convertToFirestoreDocument } from '../../services/firebase-restapi';

/**
 * Tests for Firebase REST API Service - Data Validation
 * 
 * These tests focus on the convertToFirestoreValue function and its error handling
 * for unsupported data types, as addressed in GitHub issue #49.
 */

describe('Firebase REST API - Data Validation', () => {
  describe('convertToFirestoreDocument', () => {
    describe('Supported data types', () => {
      it('should convert string values correctly', () => {
        const result = convertToFirestoreDocument({ name: 'test' });
        expect(result).toEqual({
          fields: {
            name: { stringValue: 'test' }
          }
        });
      });

      it('should convert number values correctly', () => {
        const result = convertToFirestoreDocument({ 
          age: 25, 
          price: 19.99 
        });
        expect(result).toEqual({
          fields: {
            age: { integerValue: '25' },
            price: { doubleValue: 19.99 }
          }
        });
      });

      it('should convert boolean values correctly', () => {
        const result = convertToFirestoreDocument({ 
          active: true, 
          deleted: false 
        });
        expect(result).toEqual({
          fields: {
            active: { booleanValue: true },
            deleted: { booleanValue: false }
          }
        });
      });

      it('should convert null values correctly', () => {
        const result = convertToFirestoreDocument({ value: null });
        expect(result).toEqual({
          fields: {
            value: { nullValue: null }
          }
        });
      });

      it('should convert undefined values correctly', () => {
        const result = convertToFirestoreDocument({ value: undefined });
        expect(result).toEqual({
          fields: {
            value: { nullValue: null }
          }
        });
      });

      it('should convert Date objects correctly', () => {
        const date = new Date('2023-01-01T00:00:00Z');
        const result = convertToFirestoreDocument({ createdAt: date });
        expect(result).toEqual({
          fields: {
            createdAt: { timestampValue: '2023-01-01T00:00:00.000Z' }
          }
        });
      });

      it('should convert arrays correctly', () => {
        const result = convertToFirestoreDocument({ 
          tags: ['fiction', 'drama'],
          numbers: [1, 2, 3]
        });
        expect(result).toEqual({
          fields: {
            tags: {
              arrayValue: {
                values: [
                  { stringValue: 'fiction' },
                  { stringValue: 'drama' }
                ]
              }
            },
            numbers: {
              arrayValue: {
                values: [
                  { integerValue: '1' },
                  { integerValue: '2' },
                  { integerValue: '3' }
                ]
              }
            }
          }
        });
      });

      it('should convert nested objects correctly', () => {
        const result = convertToFirestoreDocument({
          author: {
            name: 'John Doe',
            age: 30
          }
        });
        expect(result).toEqual({
          fields: {
            author: {
              mapValue: {
                fields: {
                  name: { stringValue: 'John Doe' },
                  age: { integerValue: '30' }
                }
              }
            }
          }
        });
      });

      it('should handle complex nested structures', () => {
        const result = convertToFirestoreDocument({
          book: {
            title: 'Test Book',
            authors: ['Author 1', 'Author 2'],
            metadata: {
              pages: 200,
              published: new Date('2023-01-01'),
              available: true
            }
          }
        });
        
        expect(result.fields?.book).toEqual({
          mapValue: {
            fields: {
              title: { stringValue: 'Test Book' },
              authors: {
                arrayValue: {
                  values: [
                    { stringValue: 'Author 1' },
                    { stringValue: 'Author 2' }
                  ]
                }
              },
              metadata: {
                mapValue: {
                  fields: {
                    pages: { integerValue: '200' },
                    published: { timestampValue: '2023-01-01T00:00:00.000Z' },
                    available: { booleanValue: true }
                  }
                }
              }
            }
          }
        });
      });
    });

    describe('Error handling for unsupported data types', () => {
      it('should throw error for Symbol values', () => {
        const sym = Symbol('test');
        expect(() => {
          convertToFirestoreDocument({ symbol: sym });
        }).toThrow('Unsupported data type for Firestore conversion: symbol');
      });

      it('should throw error for Function values', () => {
        const fn = () => 'test';
        expect(() => {
          convertToFirestoreDocument({ callback: fn });
        }).toThrow('Unsupported data type for Firestore conversion: function');
      });

      it('should throw error for BigInt values', () => {
        const big = BigInt(123);
        expect(() => {
          convertToFirestoreDocument({ bigNumber: big });
        }).toThrow('Unsupported data type for Firestore conversion: bigint');
      });

      it('should handle complex objects that can be JSON stringified', () => {
        // Objects like plain objects should be handled as mapValue, not stringified
        const result = convertToFirestoreDocument({
          customObj: { prop: 'value' }
        });
        expect(result).toEqual({
          fields: {
            customObj: {
              mapValue: {
                fields: {
                  prop: { stringValue: 'value' }
                }
              }
            }
          }
        });
      });

      it('should handle objects with circular references (throws RangeError)', () => {
        const circularObj: Record<string, unknown> = { name: 'test' };
        circularObj.self = circularObj; // Create circular reference
        
        // Circular references cause stack overflow - this is actually better than silent corruption
        // The improved error handling prevents silent data corruption with 'unsupported_type'
        expect(() => {
          convertToFirestoreDocument({ circular: circularObj });
        }).toThrow(RangeError);
      });

      it('should provide clear error messages with data type information', () => {
        const testCases = [
          { value: Symbol('test'), type: 'symbol' },
          { value: () => {}, type: 'function' },
          { value: BigInt(123), type: 'bigint' }
        ];

        testCases.forEach(({ value, type }) => {
          expect(() => {
            convertToFirestoreDocument({ test: value });
          }).toThrow(`Unsupported data type for Firestore conversion: ${type}`);
        });
      });
    });

    describe('Edge cases and special values', () => {
      it('should handle empty arrays', () => {
        const result = convertToFirestoreDocument({ empty: [] });
        expect(result).toEqual({
          fields: {
            empty: {
              arrayValue: {
                values: []
              }
            }
          }
        });
      });

      it('should handle empty objects', () => {
        const result = convertToFirestoreDocument({ empty: {} });
        expect(result).toEqual({
          fields: {
            empty: {
              mapValue: {
                fields: {}
              }
            }
          }
        });
      });

      it('should handle arrays with mixed types', () => {
        const result = convertToFirestoreDocument({
          mixed: ['string', 42, true, null, new Date('2023-01-01')]
        });
        
        expect(result.fields?.mixed).toEqual({
          arrayValue: {
            values: [
              { stringValue: 'string' },
              { integerValue: '42' },
              { booleanValue: true },
              { nullValue: null },
              { timestampValue: '2023-01-01T00:00:00.000Z' }
            ]
          }
        });
      });

      it('should handle zero values correctly', () => {
        const result = convertToFirestoreDocument({
          zero: 0,
          emptyString: '',
          falseBool: false
        });
        
        expect(result).toEqual({
          fields: {
            zero: { integerValue: '0' },
            emptyString: { stringValue: '' },
            falseBool: { booleanValue: false }
          }
        });
      });

      it('should handle very large numbers', () => {
        const result = convertToFirestoreDocument({
          largeInt: 9007199254740991, // Number.MAX_SAFE_INTEGER
          largeFloat: 3.14159, // A proper float value
          largeScientific: 1.7976931348623157e+308 // JavaScript treats very large numbers as integers
        });
        
        expect(result).toEqual({
          fields: {
            largeInt: { integerValue: '9007199254740991' },
            largeFloat: { doubleValue: 3.14159 },
            largeScientific: { integerValue: '1.7976931348623157e+308' }
          }
        });
      });
    });
  });
});