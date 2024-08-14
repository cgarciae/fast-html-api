
// we want to detect elements of the form
// <div hx-state="foo:Number=innerText">1</div>

class States {
  get(signals, name) {
    return signals[name].value;
  }

  set(signals, name, value) {
    signals[name].value = value;
  }
}



window.onload = () => {
  var preactSignals = window.preactSignals;
  var effects = [];

  // function traverseDOM(element) {
  document.querySelectorAll("*").forEach(function (element) {

    if (element.hasAttribute('hx-state')) {
      element.signals = {};
      element.state = new Proxy(element.signals, new States());
    }

    if (element.hasAttribute('hx-bind')) {
      var stateStr = element.getAttribute('hx-bind');
      var [propertyExpr, nameStr] = stateStr.split('=');
      if (nameStr.includes(':')) {
        var [stateName, stateType] = nameStr.split(':');
      } else {
        var stateName = nameStr;
        var stateType = '';
      }
      console.log(`stateName: ${stateName}, stateType: ${stateType}`);

      stateName = stateName.trim();
      stateType = stateType.trim();
      element._propertyPath = propertyExpr.trim().split('.');
      // get type from string
      if (stateType) {
        stateType = window[stateType];
        var initialValue = element;
        element._propertyPath.forEach(function (property) {
          initialValue = initialValue[property];
        });
        var signals = $component(element).signals;

        // if signals contains stateName, raise error
        if (signals[stateName]) {
          throw new Error(`State '${stateName}' already exists`);
        }

        signals[stateName] = preactSignals.signal(stateType(initialValue));
      }


      effects.push(function () {
        var value = element;
        var lastProperty = element._propertyPath.slice(-1)[0];
        element._propertyPath.slice(0, -1).forEach(function (property) {
          value = value[property];
        });
        // set the value
        var states = $state(this);
        value[lastProperty] = states[stateName];
      }.bind(element));
    }

    if (element.hasAttribute('hx-effect')) {
      effects.push(function () {
        return eval(this.getAttribute('hx-effect'));
      }.bind(element));
    }

    // Recursively traverse child nodes
    // var node = element.firstChild;
    // while (node) {
    //   if (node.nodeType === Node.ELEMENT_NODE) {
    //     traverseDOM(node);
    //   }
    //   node = node.nextSibling;
    // }
  });

  // traverseDOM(document.body);
  // call all the effects
  effects.forEach(effect => preactSignals.effect(effect));
};

function $component(element) {
  var node = element;
  while (node) {
    if (node.state) {
      return node;
    }
    node = node.parentNode;
  }
  // raise error
  throw new Error('No component found');
}

function $state(element) {
  return $component(element).state;
}