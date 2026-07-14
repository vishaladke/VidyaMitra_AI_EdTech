/**
 * Gateway auth middleware test stub.
 */
import jwt from 'jsonwebtoken';

const TEST_SECRET = 'test_jwt_secret';

describe('Socket JWT Auth', () => {
  it('should create a valid token', () => {
    const token = jwt.sign(
      { sub: 'test-user-id', role: 'student', type: 'access' },
      TEST_SECRET,
      { expiresIn: '30m' }
    );
    const decoded = jwt.verify(token, TEST_SECRET) as any;
    expect(decoded.sub).toBe('test-user-id');
    expect(decoded.role).toBe('student');
    expect(decoded.type).toBe('access');
  });

  it('should reject expired tokens', () => {
    const token = jwt.sign(
      { sub: 'test-user-id', role: 'student', type: 'access' },
      TEST_SECRET,
      { expiresIn: '-10s' }
    );
    expect(() => jwt.verify(token, TEST_SECRET)).toThrow();
  });

  it('should reject tokens with wrong secret', () => {
    const token = jwt.sign(
      { sub: 'test-user-id', role: 'student', type: 'access' },
      'wrong_secret'
    );
    expect(() => jwt.verify(token, TEST_SECRET)).toThrow();
  });
});
