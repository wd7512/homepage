/* Hidden icon latent slider.
 *
 * The site ships a ~3k-parameter decoder rather than precomputed frames.  Each
 * icon owns one scalar latent on a unit circle; the footer slider adds a bias
 * to every latent and the decoder redraws every pixel-art SVG on the page.
 *
 * Loaded by adapters.outbound.html, which inlines the codec JSON and this
 * file.  In Node it exports `create()` so the test-suite can replay the exact
 * arithmetic the browser runs.
 */
(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else if (typeof document !== "undefined") api.boot();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";
  var SIZE = 16;
  var PIXELS = SIZE * SIZE;

  function base64Bytes(text) {
    if (typeof atob === "function") return atob(text);
    if (typeof Buffer !== "undefined") return Buffer.from(text, "base64").toString("binary");
    throw new Error("no base64 decoder");
  }

  function int16Array(binary) {
    var out = new Int16Array(binary.length >> 1);
    for (var i = 0; i < out.length; i++) {
      var v = binary.charCodeAt(2 * i) | (binary.charCodeAt(2 * i + 1) << 8);
      out[i] = (v << 16) >> 16;
    }
    return out;
  }

  function latentFeatures(z, freqs, out) {
    for (var k = 0; k < freqs.length; k++) {
      out[k] = Math.sin(z * freqs[k]);
      out[freqs.length + k] = Math.cos(z * freqs[k]);
    }
  }

  /* Build the inference engine from a parsed codec object. */
  function create(codec) {
    if (!codec || codec.config.quant !== "i16") throw new Error("unsupported codec");
    var cfg = codec.config;
    var nf = cfg.nf;
    var np = cfg.np;
    var zFreqs = [];
    var pFreqs = [];
    for (var k = 1; k <= nf; k++) zFreqs.push(2 * Math.PI * k);
    for (var p = 1; p <= np; p++) pFreqs.push(2 * Math.PI * p);

    var zCols = nf * 2;
    var pixelCols = 2 + np * 4;
    var pixel = new Float32Array(PIXELS * pixelCols);
    for (var y = 0; y < SIZE; y++) {
      for (var x = 0; x < SIZE; x++) {
        var off = (y * SIZE + x) * pixelCols;
        pixel[off] = x / (SIZE - 1);
        pixel[off + 1] = y / (SIZE - 1);
        for (var q = 0; q < np; q++) {
          pixel[off + 2 + q] = Math.sin((x / (SIZE - 1)) * pFreqs[q]);
          pixel[off + 2 + np + q] = Math.sin((y / (SIZE - 1)) * pFreqs[q]);
          pixel[off + 2 + 2 * np + q] = Math.cos((x / (SIZE - 1)) * pFreqs[q]);
          pixel[off + 2 + 3 * np + q] = Math.cos((y / (SIZE - 1)) * pFreqs[q]);
        }
      }
    }

    var layers = codec.layers.map(function (layer) {
      var raw = int16Array(base64Bytes(layer.data));
      var weights = new Float32Array(layer["in"] * layer.out);
      for (var o = 0; o < layer.out; o++) {
        var scale = layer.scale[o];
        for (var i = 0; i < layer["in"]; i++) {
          weights[o * layer["in"] + i] = raw[o * layer["in"] + i] * scale;
        }
      }
      return {
        in: layer["in"],
        out: layer.out,
        w: weights,
        b: Float32Array.from(layer.bias),
      };
    });

    var first = layers[0];
    var second = layers[1];
    var last = layers[2];
    var hidden = first.out;
    var zf = new Float32Array(zCols);
    var z1 = new Float32Array(hidden);
    var h1 = new Float32Array(PIXELS * hidden);
    var h2 = new Float32Array(second.out);
    var cells = new Uint8Array(PIXELS);

    /* The pixel half of layer one never changes: fold it out once. */
    var p1 = new Float32Array(PIXELS * hidden);
    for (var pi = 0; pi < PIXELS; pi++) {
      for (var hi = 0; hi < hidden; hi++) {
        var sum = 0;
        var row = hi * first["in"] + zCols;
        for (var j = 0; j < pixelCols; j++) sum += pixel[pi * pixelCols + j] * first.w[row + j];
        p1[pi * hidden + hi] = sum;
      }
    }

    function decode(z) {
      z -= Math.floor(z);
      latentFeatures(z, zFreqs, zf);
      for (var h = 0; h < hidden; h++) {
        var s = first.b[h];
        for (var j = 0; j < zCols; j++) s += zf[j] * first.w[h * first["in"] + j];
        z1[h] = s;
      }
      for (var pi2 = 0; pi2 < PIXELS; pi2++) {
        var base = pi2 * hidden;
        for (var hi2 = 0; hi2 < hidden; hi2++) {
          var v = p1[base + hi2] + z1[hi2];
          h1[base + hi2] = v > 0 ? v : 0;
        }
      }
      for (var pi3 = 0; pi3 < PIXELS; pi3++) {
        var base2 = pi3 * hidden;
        for (var o = 0; o < second.out; o++) {
          var s2 = second.b[o];
          for (var i = 0; i < second["in"]; i++) s2 += h1[base2 + i] * second.w[o * second["in"] + i];
          h2[o] = s2 > 0 ? s2 : 0;
        }
        var best = 0;
        var bestValue = -Infinity;
        for (var c = 0; c < last.out; c++) {
          var s3 = last.b[c];
          for (var i2 = 0; i2 < last["in"]; i2++) s3 += h2[i2] * last.w[c * last["in"] + i2];
          if (s3 > bestValue) {
            bestValue = s3;
            best = c;
          }
        }
        cells[pi3] = best;
      }
      return cells;
    }

    function gridFor(name, phase) {
      var z = (codec.latents[name] + (phase || 0)) % 1;
      var values = decode(z);
      var out = "";
      for (var i = 0; i < PIXELS; i++) out += codec.symbols[values[i]];
      return out;
    }

    /* Run-length paths, grouped by symbol, exactly like the Python renderer. */
    function runsFor(name, phase) {
      var z = (codec.latents[name] + (phase || 0)) % 1;
      var values = decode(z);
      var runs = {};
      for (var y2 = 0; y2 < SIZE; y2++) {
        var x2 = 0;
        while (x2 < SIZE) {
          var symbol = values[y2 * SIZE + x2];
          if (codec.symbols[symbol] === ".") {
            x2++;
            continue;
          }
          var start = x2;
          while (x2 < SIZE && values[y2 * SIZE + x2] === symbol) x2++;
          var d = "M" + start + " " + y2 + "h" + (x2 - start) + "v1h-" + (x2 - start) + "z";
          if (!runs[symbol]) runs[symbol] = [];
          runs[symbol].push(d);
        }
      }
      return runs;
    }

    return { decode: decode, gridFor: gridFor, runsFor: runsFor, codec: codec };
  }

  function paintIcon(svg, engine, name, phase) {
    var runs = engine.runsFor(name, phase);
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    for (var symbol in runs) {
      if (!Object.prototype.hasOwnProperty.call(runs, symbol)) continue;
      var path = document.createElementNS(NS, "path");
      var style = engine.codec.paint[String(engine.codec.symbols[symbol])] || {};
      if (style["class"]) path.setAttribute("class", style["class"]);
      else if (style.fill) path.setAttribute("fill", style.fill);
      path.setAttribute("d", runs[symbol].join(""));
      svg.appendChild(path);
    }
  }

  function boot() {
    var payload = document.getElementById("pix-codec");
    var slider = document.getElementById("pix-z");
    if (!payload || !slider) return;

    var engine;
    try {
      engine = create(JSON.parse(payload.textContent));
    } catch (error) {
      return; // Leave the authored SVGs untouched.
    }

    var groups = {};
    var icons = document.querySelectorAll("[data-pix]");
    for (var i = 0; i < icons.length; i++) {
      var name = icons[i].getAttribute("data-pix");
      if (!(name in engine.codec.latents)) continue;
      if (!groups[name]) groups[name] = [];
      groups[name].push(icons[i]);
    }
    var names = Object.keys(groups);
    var readout = document.getElementById("pix-z-out");
    var max = Number(slider.max) || 1000;
    var phase = 0;
    var pending = null;
    var frame = 0;

    function draw(value) {
      var next = Math.max(0, Math.min(1, value / max));
      if (next === phase) return;
      phase = next;
      for (var n = 0; n < names.length; n++) {
        var nodes = groups[names[n]];
        for (var g = 0; g < nodes.length; g++) paintIcon(nodes[g], engine, names[n], phase);
      }
      slider.setAttribute("aria-valuetext", "latent " + phase.toFixed(2));
      if (readout) readout.textContent = "latent " + phase.toFixed(2);
    }

    function schedule(value) {
      pending = value;
      if (frame) return;
      frame = requestAnimationFrame(function () {
        frame = 0;
        if (pending !== null) {
          var value2 = pending;
          pending = null;
          draw(value2);
        }
      });
    }

    var initial = 0;
    try {
      var stored = localStorage.getItem("pix-z");
      if (stored !== null && stored !== "") initial = Number(stored) || 0;
    } catch (error) {
      /* private mode */
    }
    var query = new URLSearchParams(window.location.search).get("z");
    if (query !== null && query !== "") initial = Number(query) * max;
    if (!isFinite(initial)) initial = 0;
    slider.value = String(Math.max(0, Math.min(max, isFinite(initial) ? initial : 0)));
    slider.addEventListener("input", function () {
      schedule(Number(slider.value));
    });
    slider.addEventListener("change", function () {
      draw(Number(slider.value));
      try {
        localStorage.setItem("pix-z", String(slider.value));
      } catch (error) {
        /* private mode */
      }
    });

    // Restore a saved phase without animating the authored art on first paint.
    if (Number(slider.value) !== 0) draw(Number(slider.value));
  }

  return { create: create, boot: boot };
});
