function verifyArray(value: string, maxDepth = 2): boolean {
  let depth = 0

  for (const character of value)  {
    if (character == '[') {
      depth += 1
    } else if (character == ']') {
      depth -= 1
    }

    // Ensure we have not exceeded the maximum depth allowed
    if (depth > maxDepth) {
      throw 'Array too deep'
    }
  }

  return depth ==0
}

/* Converts nested arrays to a 2D array*/
function nestedArraysTo2DArray(nested: string): string {
  // Check if this is a balanced string
  if (!verifyArray(nested)) {
    // This is an issue
    throw 'Array is mal-formed'
  }

  // Replace all ],[ with ;
  return nested.replace(/]\s*,?\s*\[/g, ';')
    .replace(/\[\s*\[\s*/g, '[')
    .replace(/]\s*]\s*/g, ']')
    .replace(/\s+/g, ' ')
    .replace(/\s*,\s*/g, ', ')
}

function multiLineStringToArray(input: string): string {
  const lines = input.split('\n').map((line) => `'${line}'`)
  return `[${lines.join(';')}]`
}

export { nestedArraysTo2DArray, multiLineStringToArray}
