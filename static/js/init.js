window.onload = function() {
    var beforePan

    beforePan = function(oldPan, newPan){
      var stopHorizontal = false
        , stopVertical = false
        , gutterWidth = 100
        , gutterHeight = 100
          // Computed variables
        , sizes = this.getSizes()
        , leftLimit = -((sizes.viewBox.x + sizes.viewBox.width) * sizes.realZoom) + gutterWidth
        , rightLimit = sizes.width - gutterWidth - (sizes.viewBox.x * sizes.realZoom)
        , topLimit = -((sizes.viewBox.y + sizes.viewBox.height) * sizes.realZoom) + gutterHeight
        , bottomLimit = sizes.height - gutterHeight - (sizes.viewBox.y * sizes.realZoom)

      customPan = {}
      customPan.x = Math.max(leftLimit, Math.min(rightLimit, newPan.x))
      customPan.y = Math.max(topLimit, Math.min(bottomLimit, newPan.y))

      return customPan
    }

    // Expose to window namespace for testing purposes
    window.panZoom = svgPanZoom('#limit-svg', {
      zoomEnabled: true
    , controlIconsEnabled: true
    , fit: 1
    , center: 1
    , beforePan: beforePan
    });

    // panZoom.setBeforePan(beforePan)
  };