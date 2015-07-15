This is example client for [PDC] that provides somewhat comfortable interface
to view and edit contacts for components.

[PDC]: https://github.com/release-engineering/product-definition-center


# Usage

Hit the cog button in the top right corner, set up your servers and enjoy.


# Development

Install `npm` (probably from your package manager).

    $ npm install
    $ make
    # Builds a JS bundle ...
    # Open index.html in browser for testing

    $ make watch
    # Automatically rebuild the bundle

    $ make dist
    # create single file version in dist/index.html

If you did not install node module globally, you will need to add
`node_modules/.bin` to your `PATH`.


# Todo

* preload contact roles from the server so that user does not have to type it
  out
* add page size to server settings instead of hardcoding it
* enable obtaining token from server without manually copying it
* update to use newer dependencies (especially `react-bootstrap`)
